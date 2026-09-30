"""Port for third-party music catalogs (Spotify today, anything tomorrow).

Implementations live in ``infrastructure/spotify``; only the mapping to the
domain :class:`~migmusic.domain.entities.song.Song` is part of the contract,
so the rest of the system never sees a raw Spotify payload.

Tokens are passed per call on purpose: they are short-lived, session-scoped
and refreshed by the application layer, so a provider instance must never hold
one.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from migmusic.domain.entities.song import Song


class MusicProvider(ABC):
    """Read-only access to a remote catalog, already mapped to ``Song``."""

    @abstractmethod
    async def search_tracks(self, access_token: str, query: str, *, limit: int = 20) -> list[Song]:
        """Search the catalog and return at most ``limit`` songs."""

    @abstractmethod
    async def saved_tracks(self, access_token: str, *, limit: int = 20) -> list[Song]:
        """Return the tracks saved to the user's library."""

    @abstractmethod
    async def playlist_tracks(
        self, access_token: str, playlist_id: str, *, limit: int = 50
    ) -> list[Song]:
        """Return the tracks of one of the user's playlists."""
