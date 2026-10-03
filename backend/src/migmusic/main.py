"""Application entry point.

``create_app`` is the composition root: it is the only place where concrete
implementations are instantiated and injected.

The ASGI ``app`` object is exposed lazily (PEP 562) so that importing this
module in tests does not require a fully configured environment.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from migmusic.api.error_handlers import register_error_handlers
from migmusic.api.routers import auth, health, playback, playlists, spotify, testing, youtube
from migmusic.api.routers.auth import callback_get as legacy_callback_get
from migmusic.application.services import PlaybackService, PlaylistService
from migmusic.application.services.music_provider_registry import MusicProviderRegistry
from migmusic.application.services.spotify_auth_service import SpotifyAuthService
from migmusic.core import Settings, configure_logging, get_logger, get_settings
from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.domain.ports.playlist_repository import PlaylistRepository
from migmusic.domain.ports.token_store import TokenStore
from migmusic.infrastructure.keep_alive import (
    KEEP_ALIVE_INTERVAL_S,
    keep_alive_loop,
    keep_alive_url,
    make_pinger,
)
from migmusic.infrastructure.persistence import (
    InMemoryPlaylistRepository,
    SqlPlaylistRepository,
)
from migmusic.infrastructure.security.session_token_store import InMemoryTokenStore
from migmusic.infrastructure.security.sql_token_store import SqlTokenStore
from migmusic.infrastructure.spotify.spotify_client import SpotifyApiClient
from migmusic.infrastructure.spotify.spotify_music_provider import SpotifyMusicProvider
from migmusic.infrastructure.spotify.spotify_oauth import SpotifyOAuth
from migmusic.infrastructure.youtube.youtube_music_provider import YouTubeMusicProvider
from migmusic.infrastructure.youtube.ytmusic_client import YtMusicClient

logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application, injecting configuration explicitly."""
    config = settings if settings is not None else get_settings()
    configure_logging(config.log_level)

    # One shared HTTP client for every outbound call (Spotify auth and Web API).
    http_client = httpx.AsyncClient()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Free-tier Render sleeps after 15 idle minutes; a self-ping on the
        # public URL keeps the instance warm (dev/tests have no base URL).
        keep_alive_task: asyncio.Task[None] | None = None
        if config.render_backend_url:
            keep_alive_task = asyncio.create_task(
                keep_alive_loop(make_pinger(http_client, config.render_backend_url)),
                name="keep-alive",
            )
            logger.info(
                "keep_alive_started",
                extra={
                    "interval_s": KEEP_ALIVE_INTERVAL_S,
                    "target": keep_alive_url(config.render_backend_url),
                },
            )
        yield
        if keep_alive_task is not None:
            keep_alive_task.cancel()
            with suppress(asyncio.CancelledError):
                await keep_alive_task
        for adapter in (app.state.playlist_repository, app.state.spotify_token_store):
            if isinstance(adapter, SqlPlaylistRepository | SqlTokenStore):
                adapter.close()
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

    # Compress JSON responses (catalogs and playlists are text-heavy; this cuts
    # the wire size of a search page several times over on slow links).
    app.add_middleware(GZipMiddleware, minimum_size=512)
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
    # `DATABASE_URL` keeps the tokens across Render restarts; the in-memory
    # store would log every user out on each redeploy.
    app.state.http_client = http_client
    token_store: TokenStore
    if config.database_url:
        token_store = SqlTokenStore(config.database_url)
    else:
        token_store = InMemoryTokenStore()
    app.state.spotify_oauth = SpotifyOAuth(config.spotify)
    app.state.spotify_token_store = token_store
    app.state.spotify_auth_service = SpotifyAuthService(
        app.state.spotify_oauth, token_store, http_client
    )
    app.state.spotify_client = SpotifyApiClient(http_client)
    app.state.music_provider = SpotifyMusicProvider(app.state.spotify_client)

    # Catalog registry (Open/Closed): one adapter per remote source, built once.
    # YouTube Music is keyless and shares a single ``YTMusic`` instance; when
    # disabled the endpoint simply is not registered below.
    providers: dict[AudioSourceType, Any] = {
        AudioSourceType.SPOTIFY: app.state.music_provider,
    }
    if config.youtube_music_enabled:
        app.state.ytmusic_client = YtMusicClient(
            language=config.youtube_music_language,
            timeout=config.youtube_music_timeout_seconds,
        )
        providers[AudioSourceType.YOUTUBE] = YouTubeMusicProvider(app.state.ytmusic_client)
    app.state.music_providers = MusicProviderRegistry(providers)

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(playlists.router)
    app.include_router(playback.router)
    app.include_router(auth.router)
    app.include_router(spotify.router)
    if config.youtube_music_enabled:
        app.include_router(youtube.router)
    if not config.is_production:
        # The reset helper only exists outside production.
        app.include_router(testing.router)

    # Legacy callback endpoint for Spotify redirect URI without /spotify/
    app.add_api_route(
        "/api/auth/callback",
        legacy_callback_get,
        methods=["GET"],
        summary="OAuth callback (legacy redirect URI)",
        tags=["auth"],
    )

    logger.info(
        "application_started",
        extra={
            "app_env": config.app_env,
            "cors_origins": config.cors_origins,
            "playlist_repository": repository_adapter,
            "spotify_token_store": "sql" if config.database_url else "in_memory",
        },
    )
    return app


def __getattr__(name: str) -> Any:
    """Expose ``migmusic.main:app`` for uvicorn without eager construction."""
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
