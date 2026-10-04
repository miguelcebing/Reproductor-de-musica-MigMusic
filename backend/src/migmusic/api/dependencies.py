"""Framework-level dependencies (FastAPI ``Depends`` providers).

Services are constructed in the composition root and read from ``app.state``,
never inside routers, so tests can swap a single provider.
"""

from __future__ import annotations

import re
from typing import Annotated, cast

from fastapi import Depends, HTTPException, Request, status

from migmusic.api.spotify_session import read_session_id
from migmusic.application.services import LyricsService, PlaybackService, PlaylistService
from migmusic.application.services.music_provider_registry import MusicProviderRegistry
from migmusic.application.services.spotify_auth_service import SpotifyAuthService
from migmusic.domain.ports.music_provider import MusicProvider
from migmusic.infrastructure.spotify.spotify_client import SpotifyApiClient, token_refresher
from migmusic.infrastructure.spotify.spotify_music_provider import (
    SpotifyMusicProvider,
    current_access_token,
)


def get_playlist_service(request: Request) -> PlaylistService:
    """Return the playlist use cases attached by the composition root."""
    return cast(PlaylistService, request.app.state.playlist_service)


def get_playback_service(request: Request) -> PlaybackService:
    """Return the playback use cases attached by the composition root."""
    return cast(PlaybackService, request.app.state.playback_service)


def get_lyrics_service(request: Request) -> LyricsService:
    """Return the lyrics use cases attached by the composition root."""
    return cast(LyricsService, request.app.state.lyrics_service)


def get_spotify_auth_service(request: Request) -> SpotifyAuthService:
    """Return the OAuth use cases attached by the composition root."""
    return cast(SpotifyAuthService, request.app.state.spotify_auth_service)


def get_spotify_client(request: Request) -> SpotifyApiClient:
    """Return the Web API client attached by the composition root."""
    return cast(SpotifyApiClient, request.app.state.spotify_client)


def get_music_provider(request: Request) -> MusicProvider:
    """Return the Spotify catalog adapter (stateless, token passed per call)."""
    return cast(MusicProvider, request.app.state.music_provider)


def get_music_provider_registry(request: Request) -> MusicProviderRegistry:
    """Return the source→provider registry built by the composition root."""
    return cast(MusicProviderRegistry, request.app.state.music_providers)


DEVICE_ID_HEADER = "x-device-id"
# The frontend mints a UUID; anything longer or with control characters is a
# malformed client, not a legitimate device.
_DEVICE_ID_MIN = 8
_DEVICE_ID_MAX = 128
_DEVICE_ID_ALLOWED = re.compile(r"^[A-Za-z0-9._:-]+$")


def require_device_id(request: Request) -> str:
    """Require the caller's anonymous device id: ``X-Device-Id``.

    Every playlist and playback call is scoped to this id, so a missing or
    blank header is rejected (400) instead of silently falling back to an
    unscoped view that would expose other devices' data. This is UX isolation
    between devices, not authentication. The value is bounded and
    charset-restricted so it cannot bloat the cache or the database index.
    """
    value = request.headers.get(DEVICE_ID_HEADER, "").strip()
    if not value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-Id header is required",
        )
    if not (_DEVICE_ID_MIN <= len(value) <= _DEVICE_ID_MAX) or not _DEVICE_ID_ALLOWED.match(value):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Device-Id header is malformed",
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
    # Expose the token to the provider through the request-scoped context so
    # the MusicProvider contract stays free of Spotify-specific parameters.
    current_access_token.set(token.access_token)
    return token.access_token


PlaylistServiceDep = Annotated[PlaylistService, Depends(get_playlist_service)]
PlaybackServiceDep = Annotated[PlaybackService, Depends(get_playback_service)]
LyricsServiceDep = Annotated[LyricsService, Depends(get_lyrics_service)]
DeviceIdDep = Annotated[str, Depends(require_device_id)]
SpotifyAuthServiceDep = Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]
SpotifyClientDep = Annotated[SpotifyApiClient, Depends(get_spotify_client)]
MusicProviderDep = Annotated[MusicProvider, Depends(get_music_provider)]
MusicProviderRegistryDep = Annotated[MusicProviderRegistry, Depends(get_music_provider_registry)]


def get_spotify_provider(request: Request) -> SpotifyMusicProvider:
    """Return the Spotify adapter typed for its Spotify-only extras."""
    return cast(SpotifyMusicProvider, request.app.state.music_provider)


SpotifyProviderDep = Annotated[SpotifyMusicProvider, Depends(get_spotify_provider)]
SpotifyTokenDep = Annotated[str, Depends(require_spotify_token)]
