"""Test the shared playlist utilities."""
import uuid
from unittest.mock import patch

import pytest
from moomoo_http.playlist_generator import BasePlaylistGenerator, Playlist, Track
from moomoo_http.routes.playlist import PlaylistArgs, make_http_response
from werkzeug.datastructures import TypeConversionDict

from ...conftest import load_local_files_table


class FakePlaylistGenerator(BasePlaylistGenerator):
    """Fake playlist generator."""

    name = "fake"

    def get_playlist(self, limit: int, **_) -> Playlist:
        """Fake playlist generator."""
        return Playlist(
            playlist=[
                Track(
                    filepath=f"test/{i}",
                    artist_mbid=None,
                    album_artist_mbid=None,
                    distance=None,
                )
                for i in range(limit)
            ]
        )


@pytest.fixture(autouse=True)
def load_local_files_table__fixed():
    """Preload each test with a local files table."""
    data = [
        dict(filepath=f"test/{i}", embedding=str([i] * 10), artist_mbid=uuid.uuid4())
        for i in range(10)
    ]
    load_local_files_table(data=data)


def test_playlist_args__from_request():
    """Test the playlist args from request constructor."""

    class Request:
        """Fake request."""

        args = None

    request = Request()

    request.args = TypeConversionDict(n="0", seed="0", shuffle="0")
    args = PlaylistArgs.from_request(request)
    assert args.n == 0
    assert args.seed == 0
    assert args.shuffle is False

    request.args = TypeConversionDict(n="1", seed="1", shuffle="true")
    args = PlaylistArgs.from_request(request)
    assert args.n == 1
    assert args.seed == 1
    assert args.shuffle is True


def test_make_http_response():
    """Test the make http response function."""
    generators = [FakePlaylistGenerator() for _ in range(3)]
    args = PlaylistArgs(n=3, seed=0, shuffle=True)
    res = make_http_response(generators=generators, args=args)
    assert res.json["success"]
    assert len(res.json["playlists"]) == 3
    assert all(len(plist["playlist"]) == 3 for plist in res.json["playlists"])

    # single error on get_playlist gets skipped
    with patch.object(generators[0], "get_playlist", side_effect=Exception("test")):
        res = make_http_response(generators=generators, args=args)
        assert res.json["success"]
        assert len(res.json["playlists"]) == 2

    # error raised if no playlists are generated
    with patch.object(
        FakePlaylistGenerator, "get_playlist", side_effect=Exception("test")
    ):
        res = make_http_response(generators=generators, args=args)
        assert not res.json["success"]
        assert res.json["error"] == "Exception: test"
