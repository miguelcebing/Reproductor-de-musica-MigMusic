"""Domain rule violations raised by entities and structures.

All of them inherit from the ``core`` base errors, so ``api/error_handlers.py``
can translate them into HTTP responses in a single place:

===========================  ======  ==================
Exception                    Status  Code
===========================  ======  ==================
``EmptyPlaylistError``       400     ``domain_error``
``InvalidPositionError``     422     ``validation_error``
``ItemNotFoundError``        404     ``not_found``
===========================  ======  ==================
"""

from __future__ import annotations

from migmusic.core import DomainError, NotFoundError, ValidationError


class EmptyPlaylistError(DomainError):
    """Raised when an operation needs at least one song and the list is empty."""


class InvalidPositionError(ValidationError):
    """Raised when a position is outside ``0 .. size``."""

    def __init__(self, position: int, size: int) -> None:
        super().__init__(f"position {position} is out of range for a list of size {size}")
        self.position = position
        self.size = size


class ItemNotFoundError(NotFoundError):
    """Raised when the song to remove or locate is not in the list."""
