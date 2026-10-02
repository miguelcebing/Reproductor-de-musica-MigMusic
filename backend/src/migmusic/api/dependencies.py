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


def get_device_id(request: Request) -> str | None:
    """Optional device scope: ``X-Device-Id`` narrows playlist visibility.

    Missing or blank means "unscoped" (``None``): the caller sees every
    playlist. This is UX isolation for local lists, not authentication — the
    header is advisory and cheap to omit in tooling and curl checks.
    """
    value = request.headers.get(DEVICE_ID_HEADER, "").strip()
    return value or None


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
DeviceIdDep = Annotated[str | None, Depends(get_device_id)]
SpotifyAuthServiceDep = Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]
SpotifyClientDep = Annotated[SpotifyApiClient, Depends(get_spotify_client)]
MusicProviderDep = Annotated[MusicProvider, Depends(get_music_provider)]
SpotifyTokenDep = Annotated[str, Depends(require_spotify_token)]
