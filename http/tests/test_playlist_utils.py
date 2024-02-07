"""Test the base app."""

from uuid import uuid4

from moomoo_http.routes.playlist import PlaylistResponse, collection_item_to_playlist
from moomoo_playlist import Playlist, Track
from moomoo_playlist.ddl import PlaylistCollectionItem


def test_collection_item_to_playlist():
    ci = PlaylistCollectionItem(
        collection_id=uuid4(),
        collection_order_index=0,
        title="test",
        description="test",
        playlist=[],
    )

    p = collection_item_to_playlist(ci)
    assert p.title == "test"
    assert p.description == "test"
    assert p.tracks == []
    assert p.seeds == []

    recording_mbid = uuid4()
    ci = PlaylistCollectionItem(
        collection_id=uuid4(),
        collection_order_index=0,
        title="test",
        description="test",
        playlist=[{"filepath": "test.mp3", "recording_mbid": recording_mbid}],
    )

    p = collection_item_to_playlist(ci)
    assert p.title == "test"
    assert p.description == "test"
    assert p.tracks == [Track(filepath="test.mp3", recording_mbid=recording_mbid)]
    assert p.seeds == []


def test_PlaylistResponse__serialize_playlist():
    p = Playlist(tracks=[Track(filepath="test.mp3")])
    res = PlaylistResponse.serialize_playlist(p)
    assert res == {"playlist": [{"filepath": "test.mp3"}]}

    p.title = "test"
    p.description = "test"
    res = PlaylistResponse.serialize_playlist(p)
    assert res == {
        "playlist": [{"filepath": "test.mp3"}],
        "title": "test",
        "description": "test",
    }


def test_PlaylistResponse__to_serializable():
    pr = PlaylistResponse(
        success=True, playlists=[Playlist(tracks=[Track(filepath="test.mp3")])]
    )
    res = pr.to_serializable()
    assert res == {
        "success": True,
        "playlists": [{"playlist": [{"filepath": "test.mp3"}]}],
    }

    pr = PlaylistResponse(success=False, error="test")
    res = pr.to_serializable()
    assert res == {"success": False, "error": "test"}


def test_PlaylistResponse__to_http():
    pr = PlaylistResponse(
        success=True, playlists=[Playlist(tracks=[Track(filepath="test.mp3")])]
    )
    res = pr.to_http()
    assert res.status_code == 200
    assert res.content_type == "application/json"
    assert res.json == {
        "success": True,
        "playlists": [{"playlist": [{"filepath": "test.mp3"}]}],
    }

    pr = PlaylistResponse(success=False, error="test")
    res = pr.to_http()
    assert res.status_code == 500
    assert res.content_type == "application/json"
    assert res.json == {"success": False, "error": "test"}