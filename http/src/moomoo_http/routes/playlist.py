"""Blueprint for the /playlist endpoint.

Use the base postgres connection in the playlist module for now. eventually should 
use a sqlalchemy session.
"""
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path

from flask import Blueprint, Request, request
from sqlalchemy.orm import Session

from ..db import MoomooPlaylist, db
from ..playlist_generator import PlaylistGenerator
from .logger import get_logger

logger = get_logger(__name__)


bp = Blueprint("playlist", __name__, url_prefix="/playlist")


def boolean_type(v: str) -> bool:
    """Convert a string to a boolean."""
    return v.lower() in ["1", "true"]


@dataclass
class PlaylistArgs:
    """Dataclass for common playlist arguments."""

    n: int
    seed: int
    shuffle: bool

    @classmethod
    def from_request(cls, request: Request) -> "PlaylistArgs":
        """Create a PlaylistArgs object from a request."""
        return cls(
            n=request.args.get("n", 20, type=int),
            seed=request.args.get("seed", 0, type=int),
            shuffle=request.args.get("shuffle", "1", type=boolean_type),
        )


def try_insert(plist: MoomooPlaylist, session: Session) -> None:
    """Try to insert a playlist and log on error (not raising)."""
    try:
        session.add(plist)
        session.commit()
        logger.info("Inserted playlist.")
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        logger.error(f"Failed to insert playlist: {type(e).__name__}: {e}")


@bp.route("/from-files", methods=["GET"])
def from_files():
    """Create a playlist from one or more files."""
    args = PlaylistArgs.from_request(request)
    paths = request.args.getlist("path", type=Path)
    username = request.headers.get("listenbrainz-username")

    if username is None:
        return (
            {"success": False, "error": "No listenbrainz-username header provided."},
            400,
        )
    if len(paths) == 0:
        return ({"success": False, "error": "No filepaths provided."}, 400)
    elif len(paths) > 500:
        return {"success": False, "error": "Too many filepaths provided (>500)."}, 400

    logger.info(f"playlist request: {username} / {paths} ({args})")

    try:
        generator = PlaylistGenerator.from_files(paths)
        plist_paths, source_paths = generator.get_playlist(
            limit=args.n,
            shuffle=args.shuffle,
            seed_count=args.seed,
            session=db.session,
        )
    except Exception as e:
        traceback.print_exc(file=sys.stdout)
        return ({"success": False, "error": f"{type(e).__name__}: {e}"}, 500)

    # exit early if we don't want to store the playlist
    plist_strs = list(map(str, plist_paths))
    source_strs = list(map(str, source_paths))

    db_plist = MoomooPlaylist(
        username=username,
        generator="from-files",
        playlist=plist_strs,
        source_paths=source_strs,
    )
    try_insert(db_plist, session=db.session)

    return {"success": True, "playlist": plist_strs, "source_paths": source_strs}
