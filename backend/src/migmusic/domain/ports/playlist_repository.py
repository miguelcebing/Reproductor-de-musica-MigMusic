"""Persistence contract for the ``Playlist`` aggregate.

Defined in the domain and implemented by adapters (``InMemory...``,
``SqlPlaylistRepository``), so services depend on behaviour, not on a database.

Every method receives an ``owner_id`` on purpose: a query or a write that does
not name an owner cannot be expressed, which makes it impossible to forget the
device scope in an endpoint.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from migmusic.domain.entities.playlist import Playlist


class PlaylistRepository(ABC):
    """Store and retrieve playlists as whole aggregates, scoped to one owner."""

    @abstractmethod
    def save(self, playlist: Playlist, *, owner_id: str) -> None:
        """Insert or update ``playlist`` (upsert on :attr:`Playlist.id`).

        ``owner_id`` stamps the device the playlist belongs to on its *first*
        write; later writes keep the owner they already have, so an edit can
        never re-home a playlist to another device.
        """

    @abstractmethod
    def find_by_id(self, playlist_id: str, *, owner_id: str) -> Playlist | None:
        """Return the playlist with ``playlist_id`` when ``owner_id`` owns it.

        A playlist that exists but belongs to another device is reported as
        ``None`` (the API answers 404), so foreign ids are not enumerable.
        """

    @abstractmethod
    def list_all(self, *, owner_id: str) -> list[Playlist]:
        """Return every playlist owned by ``owner_id``, in insertion order."""

    @abstractmethod
    def delete(self, playlist_id: str, *, owner_id: str) -> bool:
        """Remove the playlist; ``False`` when it did not exist for ``owner_id``."""

    @abstractmethod
    def delete_all(self) -> int:
        """Remove every playlist (development and test reset only).

        Never wired to a public production endpoint; the composition root only
        exposes it through the dev-only testing router.
        """
