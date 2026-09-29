"""Persistence contract for the ``Playlist`` aggregate.

Defined in the domain and implemented by adapters (``InMemory...``,
``SqlPlaylistRepository``), so services depend on behaviour, not on a database.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from migmusic.domain.entities.playlist import Playlist


class PlaylistRepository(ABC):
    """Store and retrieve playlists as whole aggregates."""

    @abstractmethod
    def save(self, playlist: Playlist) -> None:
        """Insert or update ``playlist`` (upsert on :attr:`Playlist.id`)."""

    @abstractmethod
    def find_by_id(self, playlist_id: str) -> Playlist | None:
        """Return the playlist with ``playlist_id``, or ``None`` when absent."""

    @abstractmethod
    def list_all(self) -> list[Playlist]:
        """Return every stored playlist, in insertion order."""

    @abstractmethod
    def delete(self, playlist_id: str) -> bool:
        """Remove the playlist; ``False`` when it did not exist."""
