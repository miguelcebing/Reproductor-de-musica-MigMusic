"""Application entry point.

``create_app`` is the composition root: it is the only place where concrete
implementations are instantiated and injected.

The ASGI ``app`` object is exposed lazily (PEP 562) so that importing this
module in tests does not require a fully configured environment.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from migmusic.api.error_handlers import register_error_handlers
from migmusic.api.routers import health, playback, playlists
from migmusic.application.services import PlaybackService, PlaylistService
from migmusic.core import Settings, configure_logging, get_logger, get_settings
from migmusic.infrastructure.persistence import InMemoryPlaylistRepository

logger = get_logger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the FastAPI application, injecting configuration explicitly."""
    config = settings if settings is not None else get_settings()
    configure_logging(config.log_level)

    app = FastAPI(
        title="MigMusic API",
        version="0.1.0",
        # Interactive docs are open in development only.
        docs_url=None if config.is_production else "/docs",
        redoc_url=None if config.is_production else "/redoc",
        openapi_url=None if config.is_production else "/openapi.json",
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
    repository = InMemoryPlaylistRepository()
    app.state.playlist_repository = repository
    app.state.playlist_service = PlaylistService(repository)
    app.state.playback_service = PlaybackService(repository, skip_seconds=config.skip_seconds)

    register_error_handlers(app)
    app.include_router(health.router)
    app.include_router(playlists.router)
    app.include_router(playback.router)

    logger.info(
        "application_started",
        extra={"app_env": config.app_env, "cors_origins": config.cors_origins},
    )
    return app


def __getattr__(name: str) -> Any:
    """Expose ``migmusic.main:app`` for uvicorn without eager construction."""
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
