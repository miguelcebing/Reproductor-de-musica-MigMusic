"""Development and test helpers.

Mounted only when ``APP_ENV != production`` (see ``main.create_app``): the
production deployment never exposes a way to wipe every playlist. The E2E
suite uses it to start from a clean repository now that ``GET /api/playlists``
requires an ``X-Device-Id`` and only ever returns the caller's own data.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from migmusic.domain.ports.playlist_repository import PlaylistRepository

router = APIRouter(prefix="/api/testing", tags=["testing"])


@router.post("/reset", summary="Delete every playlist (dev/test only)")
def reset(request: Request) -> dict[str, int]:
    """Wipe the playlist store and report how many rows were removed."""
    repository: PlaylistRepository = request.app.state.playlist_repository
    return {"deleted": repository.delete_all()}
