"""Health endpoints used by uptime probes and the CI smoke test."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["health"])


@router.get("/api/health", summary="Liveness and readiness probe")
async def health(request: Request) -> JSONResponse:
    """Report service status without touching Spotify or the database."""
    settings = request.app.state.settings
    return JSONResponse(
        status_code=200,
        content={
            "status": "ok",
            "service": "migmusic",
            "environment": settings.app_env,
        },
    )
