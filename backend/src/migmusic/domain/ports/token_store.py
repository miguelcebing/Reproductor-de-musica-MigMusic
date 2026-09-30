"""Port for storing Spotify tokens per session (``SKILL3``)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class TokenBundle:
    """Stored token data for one session."""

    access_token: str
    refresh_token: str
    expires_at: float
    scope: str


class TokenStore(ABC):
    """Abstract store for Spotify tokens, keyed by session."""

    @abstractmethod
    async def get(self, session_id: str) -> TokenBundle | None:
        """Return the token bundle for a session, or None if none stored."""

    @abstractmethod
    async def set(self, session_id: str, bundle: TokenBundle) -> None:
        """Store or update the token bundle for a session."""

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Remove tokens for a session (logout)."""
