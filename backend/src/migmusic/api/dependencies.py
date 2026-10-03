"""Framework-level dependencies (FastAPI ``Depends`` providers).

Services are constructed in the composition root and read from ``app.state``,
never inside routers, so tests can swap a single provider.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status

from migmusic.api.spotify_session import read_session_id
from migmusic.application.services import PlaybackService, PlaylistService
from migmusic.application.services.spotify_auth_service import SpotifyAuthService
from migmusic.domain.ports.music_provider import MusicProvider
from migmusic.infrastructure.spotify.spotify_client import SpotifyApiClient, token_refresher


def get_playlist_service(request: Request) -> PlaylistService:
    """Return the playlist use cases attached by the composition root."""
    return cast(PlaylistService, request.app.state.playlist_service)


def get_playback_service(request: Request) -> PlaybackService:
    """Return the playback use cases attached by the composition root."""
    return cast(PlaybackService, request.app.state.playback_service)


def get_spotify_auth_service(request: Request) -> SpotifyAuthService:
    """Return the OAuth use cases attached by the composition root."""
    return cast(SpotifyAuthService, request.app.state.spotify_auth_service)


def get_spotify_client(request: Request) -> SpotifyApiClient:
    """Return the Web API client attached by the composition root."""
    return cast(SpotifyApiClient, request.app.state.spotify_client)


def get_music_provider(request: Request) -> MusicProvider:
    """Return the Spotify catalog adapter (stateless, token passed per call)."""
    return cast(MusicProvider, request.app.state.music_provider)


DEVICE_ID_HEADER = "x-device-id"


def require_device_id(request: Request) -> str:
    """Require the caller's anonymous device id: ``X-Device-Id``.

    Every playlist and playback call is scoped to this id, so a missing or
    blank header is rejected (400) instead of silently falling back to an
    unscoped view that would expose other devices' data. This is UX isolation
    between devices, not authentication.
    """
    value = request.headers.get(DEVICE_ID_HEADER, "").strip()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-Id header is required",
        )
    return value


async def require_spotify_token(
    request: Request,
    service: Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)],
) -> str:
    """Resolve a fresh access token or answer ``401`` so the UI reconnects."""
    session_id = read_session_id(request)
    token = await service.valid_access_token(session_id) if session_id else None
    if token is None or session_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Spotify is not connected; sign in first",
        )
    # Let the Web API client renew this session's token when a 401 arrives
    # despite the proactive refresh (clock skew, early invalidation).
    token_refresher.set(lambda: service.force_refresh(session_id))
    return token.access_token


PlaylistServiceDep = Annotated[PlaylistService, Depends(get_playlist_service)]
PlaybackServiceDep = Annotated[PlaybackService, Depends(get_playback_service)]
DeviceIdDep = Annotated[str, Depends(require_device_id)]
SpotifyAuthServiceDep = Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]
SpotifyClientDep = Annotated[SpotifyApiClient, Depends(get_spotify_client)]
MusicProviderDep = Annotated[MusicProvider, Depends(get_music_provider)]
SpotifyTokenDep = Annotated[str, Depends(require_spotify_token)]
