"""In-memory adapter for the :class:`PlaylistRepository` port.

Development and test default: playlists live in a dict for the life of the
process. Swapping in ``SqlPlaylistRepository`` (``DB-002``, deferred to F10)
does not touch any service, which is exactly what the port is for.

Ownership is part of every operation: the owner is recorded on the first write
and consulted on every read, edit and delete.
"""

from __future__ import annotations

import threading

from migmusic.domain.entities.playlist import Playlist
from migmusic.domain.ports.playlist_repository import PlaylistRepository


class InMemoryPlaylistRepository(PlaylistRepository):
    """Dict-backed repository; safe for concurrent request handlers."""

    def __init__(self) -> None:
        """Start with an empty store guarded by a re-entrant lock."""
        self._items: dict[str, Playlist] = {}
        self._owners: dict[str, str] = {}
        self._lock = threading.RLock()

    def save(self, playlist: Playlist, *, owner_id: str) -> None:
        """Upsert ``playlist`` keyed by :attr:`Playlist.id` — O(1).

        The owner is decided by the first write, mirroring the SQL adapter's
        ``ON CONFLICT`` clause: later saves never move a playlist sideways.
        """
        with self._lock:
            # First write fixes the insertion order used by ``list_all``.
            self._items[playlist.id] = playlist
            self._owners.setdefault(playlist.id, owner_id)

    def find_by_id(self, playlist_id: str, *, owner_id: str) -> Playlist | None:
        """Return the playlist when ``owner_id`` owns it, else ``None`` — O(1)."""
        with self._lock:
            if self._owners.get(playlist_id) != owner_id:
                return None
            return self._items.get(playlist_id)

    def list_all(self, *, owner_id: str) -> list[Playlist]:
        """Every playlist owned by ``owner_id``, in insertion order — O(n)."""
        with self._lock:
            return [
                playlist
                for playlist in self._items.values()
                if self._owners.get(playlist.id) == owner_id
            ]

    def delete(self, playlist_id: str, *, owner_id: str) -> bool:
        """Remove the playlist when ``owner_id`` owns it — O(1)."""
        with self._lock:
            if self._owners.get(playlist_id) != owner_id:
                return False
            self._owners.pop(playlist_id, None)
            return self._items.pop(playlist_id, None) is not None

    def delete_all(self) -> int:
        """Drop every playlist and owner stamp (development/test reset) — O(n)."""
        with self._lock:
            count = len(self._items)
            self._items.clear()
            self._owners.clear()
            return count


__all__ = ["InMemoryPlaylistRepository"]
