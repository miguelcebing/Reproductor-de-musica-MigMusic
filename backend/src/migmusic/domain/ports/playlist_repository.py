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
    def save(self, playlist: Playlist, *, owner_id: str | None = None) -> None:
        """Insert or update ``playlist`` (upsert on :attr:`Playlist.id`).

        ``owner_id`` stamps the device the playlist belongs to on its *first*
        write; later writes keep the owner they already have.
        """

    @abstractmethod
    def find_by_id(self, playlist_id: str) -> Playlist | None:
        """Return the playlist with ``playlist_id``, or ``None`` when absent."""

    @abstractmethod
    def list_all(self, *, owner_id: str | None = None) -> list[Playlist]:
        """Return every stored playlist, in insertion order.

        ``owner_id`` narrows the scope to one device; ``None`` returns all of
        them (the unscoped view used by tooling and the smoke checks).
        """

    @abstractmethod
    def delete(self, playlist_id: str) -> bool:
        """Remove the playlist; ``False`` when it did not exist."""
