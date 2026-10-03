"""Errors raised by the YouTube Music adapter."""

from __future__ import annotations

from migmusic.core import ExternalServiceError


class YouTubeMusicError(ExternalServiceError):
    """YouTube Music could not answer (network, blocked, rate limited)."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message, service="YouTube Music", status_code=status_code)


__all__ = ["YouTubeMusicError"]
