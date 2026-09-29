"""Framework-level dependencies (FastAPI ``Depends`` providers).

Services are constructed in the composition root and read from ``app.state``,
never inside routers, so tests can swap a single provider.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, Request

from migmusic.application.services import PlaybackService, PlaylistService


def get_playlist_service(request: Request) -> PlaylistService:
    """Return the playlist use cases attached by the composition root."""
    return cast(PlaylistService, request.app.state.playlist_service)


def get_playback_service(request: Request) -> PlaybackService:
    """Return the playback use cases attached by the composition root."""
    return cast(PlaybackService, request.app.state.playback_service)


PlaylistServiceDep = Annotated[PlaylistService, Depends(get_playlist_service)]
PlaybackServiceDep = Annotated[PlaybackService, Depends(get_playback_service)]
