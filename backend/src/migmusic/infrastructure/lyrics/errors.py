"""Errors raised by the LRCLIB adapter."""

from __future__ import annotations

from migmusic.core import ExternalServiceError


class LrclibError(ExternalServiceError):
    """LRCLIB could not answer (network, timeout, malformed payload)."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message, service="LRCLIB", status_code=status_code)


__all__ = ["LrclibError"]
