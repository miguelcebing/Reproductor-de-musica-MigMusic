"""In-memory token store for development (``SKILL3``).

Production should swap this for a Redis/DB-backed implementation.
Tokens are never written to localStorage or exposed to the frontend.
"""

from __future__ import annotations

import asyncio

from migmusic.domain.ports.token_store import TokenBundle, TokenStore


class InMemoryTokenStore(TokenStore):
    """Simple dict-backed store with async API for parity with production."""

    def __init__(self) -> None:
        self._store: dict[str, TokenBundle] = {}
        self._lock = asyncio.Lock()

    async def get(self, session_id: str) -> TokenBundle | None:
        async with self._lock:
            return self._store.get(session_id)

    async def set(self, session_id: str, bundle: TokenBundle) -> None:
        async with self._lock:
            self._store[session_id] = bundle

    async def delete(self, session_id: str) -> None:
        async with self._lock:
            self._store.pop(session_id, None)
