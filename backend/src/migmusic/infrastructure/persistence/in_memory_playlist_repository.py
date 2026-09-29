"""In-memory adapter for the :class:`PlaylistRepository` port.

Development and test default: playlists live in a dict for the life of the
process. Swapping in ``SqlPlaylistRepository`` (``DB-002``, deferred to F10)
does not touch any service, which is exactly what the port is for.
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
        self._lock = threading.RLock()

    def save(self, playlist: Playlist) -> None:
        """Upsert ``playlist`` keyed by :attr:`Playlist.id` — O(1)."""
        with self._lock:
            # First write fixes the insertion order used by ``list_all``.
            self._items[playlist.id] = playlist

    def find_by_id(self, playlist_id: str) -> Playlist | None:
        """Return the stored playlist, or ``None`` — O(1)."""
        with self._lock:
            return self._items.get(playlist_id)

    def list_all(self) -> list[Playlist]:
        """Every playlist in insertion order — O(n)."""
        with self._lock:
            return list(self._items.values())

    def delete(self, playlist_id: str) -> bool:
        """Remove the playlist; ``False`` when it was not stored — O(1)."""
        with self._lock:
            return self._items.pop(playlist_id, None) is not None


__all__ = ["InMemoryPlaylistRepository"]
