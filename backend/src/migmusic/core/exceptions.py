"""Base exceptions.

Domain-specific errors live in ``migmusic.domain.exceptions``; these are the
cross-cutting ones shared by every layer.
"""

from __future__ import annotations


class MigMusicError(Exception):
    """Base class for every error raised by MigMusic."""


class ConfigurationError(MigMusicError):
    """Raised when required configuration is missing or invalid."""


class DomainError(MigMusicError):
    """Base class for domain rule violations.

    The API layer maps subclasses of this to HTTP responses in a single place
    (``api/error_handlers.py``) instead of catching them in every router.
    """


class NotFoundError(DomainError):
    """Raised when a requested entity does not exist."""


class ValidationError(DomainError):
    """Raised when input violates a domain invariant."""


class ExternalServiceError(MigMusicError):
    """Raised when an upstream dependency (Spotify, database) fails."""

    def __init__(self, message: str, *, service: str, status_code: int | None = None) -> None:
        """Store the failing service and its HTTP status, if known."""
        super().__init__(message)
        self.service = service
        self.status_code = status_code
