"""Typed errors raised by the Spotify Web API adapter.

All of them subclass :class:`ExternalServiceError`, so ``error_handlers.py``
turns them into HTTP responses without any router knowing about Spotify.
"""

from __future__ import annotations

from migmusic.core import ExternalServiceError


class SpotifyApiError(ExternalServiceError):
    """A Web API call failed (4xx/5xx, malformed body, timeout)."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message, service="spotify", status_code=status_code)


class SpotifyAuthError(SpotifyApiError):
    """The access token was rejected (expired, revoked, wrong scope)."""


class SpotifyRateLimitError(SpotifyApiError):
    """Spotify answered 429; callers may wait ``retry_after`` seconds."""

    def __init__(self, retry_after: int) -> None:
        super().__init__(f"Spotify rate limit; retry after {retry_after}s", status_code=429)
        self.retry_after = retry_after


__all__ = ["SpotifyApiError", "SpotifyAuthError", "SpotifyRateLimitError"]
