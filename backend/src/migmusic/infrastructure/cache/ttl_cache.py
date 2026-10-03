"""A tiny in-memory cache with a time-to-live per entry.

Used for catalog searches and lyrics: the same query is asked repeatedly (the
UI debounces but the user still retypes), and every miss is a network round
trip to an unofficial API. Thread-safe because the YouTube adapter fills it
from a worker thread.
"""

from __future__ import annotations

import threading
import time
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class TtlCache(Generic[K, V]):
    """Dict-backed cache where every entry expires ``ttl`` seconds after write."""

    def __init__(self, *, ttl: float, max_size: int = 256) -> None:
        if ttl <= 0:
            raise ValueError("ttl must be positive")
        if max_size <= 0:
            raise ValueError("max_size must be positive")
        self._ttl = ttl
        self._max_size = max_size
        self._items: dict[K, tuple[float, V]] = {}
        self._lock = threading.Lock()

    def get(self, key: K) -> V | None:
        """Return the live value for ``key``, or ``None`` when missing/expired."""
        with self._lock:
            entry = self._items.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if expires_at <= time.monotonic():
                del self._items[key]
                return None
            return value

    def set(self, key: K, value: V) -> None:
        """Store ``value`` under ``key``, evicting the oldest entry when full."""
        with self._lock:
            if key not in self._items and len(self._items) >= self._max_size:
                self._evict_locked()
            self._items[key] = (time.monotonic() + self._ttl, value)

    def clear(self) -> None:
        """Drop every entry (tests)."""
        with self._lock:
            self._items.clear()

    def _evict_locked(self) -> None:
        """Remove the entry closest to expiry (approximate LRU by insert time)."""
        oldest_key = min(self._items, key=lambda item: self._items[item][0])
        del self._items[oldest_key]


__all__ = ["TtlCache"]
