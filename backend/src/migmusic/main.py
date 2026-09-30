"""Application entry point.

``create_app`` is the composition root: it is the only place where concrete
implementations are instantiated and injected.

The ASGI ``app`` object is exposed lazily (PEP 562) so that importing this
module in tests does not require a fully configured environment.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from migmusic.api.error_handlers import register_error_handlers
from migmusic.api.routers import auth, health, playback, playlists, spotify
from migmusic.application.services import PlaybackService, PlaylistService
from migmusic.application.services.spotify_auth_service import SpotifyAuthService
from migmusic.core import Settings, configure_logging, get_logger, get_settings
from migmusic.domain.ports.playlist_repository import PlaylistRepository
from migmusic.infrastructure.persistence import (
    InMemoryPlaylistRepository,
    SqlPlaylistRepository,
)
from migmusic.infrastructure.security.session_token_store import InMemoryTokenStore
from migmusic.infrastructure.spotify.spotify_client import SpotifyApiClient
from migmusic.infrastructure.spotify.spotify_music_provider import SpotifyMusicProvider
from migmusic.infrastructure.spotify.spotify_oauth import SpotifyOAuth

logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application, injecting configuration explicitly."""
    config = settings if settings is not None else get_settings()
    configure_logging(config.log_level)

    # One shared HTTP client for every outbound call (Spotify auth and Web API).
    http_client = httpx.AsyncClient()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        await http_client.aclose()

    app = FastAPI(
        title="MigMusic API",
        version="0.1.0",
        # Interactive docs are open in development only.
        docs_url=None if config.is_production else "/docs",
        redoc_url=None if config.is_production else "/redoc",
        openapi_url=None if config.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.state.settings = config
    app.state.logger = logger

    # Composition root: the only place where adapters are instantiated.
    # `DATABASE_URL` picks PostgreSQL (`DB-002`); without it the app keeps the
    # in-memory adapter used by development and tests.
    repository: PlaylistRepository
    if config.database_url:
        repository = SqlPlaylistRepository(config.database_url)
        repository_adapter = "sql"
    else:
        repository = InMemoryPlaylistRepository()
        repository_adapter = "in_memory"
    app.state.playlist_repository = repository
    app.state.playlist_service = PlaylistService(repository)
    app.state.playback_service = PlaybackService(repository, skip_seconds=config.skip_seconds)

    # Spotify: a session-scoped token store and the catalog adapter
    # (stateless: the access token travels per call).
    app.state.http_client = http_client
    token_store = InMemoryTokenStore()
    app.state.spotify_oauth = SpotifyOAuth(config.spotify)
    app.state.spotify_token_store = token_store
    app.state.spotify_auth_service = SpotifyAuthService(
        app.state.spotify_oauth, token_store, http_client
    )
    app.state.spotify_client = SpotifyApiClient(http_client)
    app.state.music_provider = SpotifyMusicProvider(app.state.spotify_client)

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(playlists.router)
    app.include_router(playback.router)
    app.include_router(auth.router)
    app.include_router(spotify.router)

    logger.info(
        "application_started",
        extra={
            "app_env": config.app_env,
            "cors_origins": config.cors_origins,
            "playlist_repository": repository_adapter,
        },
    )
    return app


def __getattr__(name: str) -> Any:
    """Expose ``migmusic.main:app`` for uvicorn without eager construction."""
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
