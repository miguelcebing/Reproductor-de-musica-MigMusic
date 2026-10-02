"""PostgreSQL adapter for the :class:`TokenStore` port.

The in-memory store dies with the process: every Render restart (deploys,
free-tier idle restarts, crashes) silently logged every user out and forced a
fresh Spotify re-link. Tokens therefore live in the same Neon database as the
playlists whenever ``DATABASE_URL`` is configured; development and the test
suite keep :class:`InMemoryTokenStore`.

SQL runs in a worker thread (``asyncio.to_thread``) so the adapter stays
non-blocking for the event loop without psycopg's async mode, which cannot use
Windows' default ``ProactorEventLoop``.

Tokens are secrets: the rows are never exposed to the frontend, and the table
holds nothing but what Spotify issued (``SKILL3``).
"""

from __future__ import annotations

import asyncio
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from migmusic.domain.ports.token_store import TokenBundle, TokenStore

# Idempotent schema: safe to run on every process start (`IF NOT EXISTS`).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS spotify_tokens (
    session_id TEXT PRIMARY KEY,
    access_token TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    expires_at DOUBLE PRECISION NOT NULL,
    scope TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_UPSERT = """
INSERT INTO spotify_tokens (session_id, access_token, refresh_token, expires_at, scope)
VALUES (%(session_id)s, %(access_token)s, %(refresh_token)s, %(expires_at)s, %(scope)s)
ON CONFLICT (session_id) DO UPDATE SET
    access_token = EXCLUDED.access_token,
    refresh_token = EXCLUDED.refresh_token,
    expires_at = EXCLUDED.expires_at,
    scope = EXCLUDED.scope,
    updated_at = now()
"""


class SqlTokenStore(TokenStore):
    """Database-backed token store; one short transaction per operation.

    Connections come from a small pool: the token lookup rides on every
    Spotify search, and a fresh TCP+TLS handshake to Neon per call showed up
    as hundreds of milliseconds of avoidable latency.
    """

    def __init__(self, dsn: str) -> None:
        """Create the connection pool and the schema on startup."""
        if not dsn.strip():
            raise ValueError("database DSN must not be empty")
        self._pool = ConnectionPool[psycopg.Connection[dict[str, Any]]](
            conninfo=dsn,
            min_size=0,
            max_size=5,
            kwargs={"row_factory": dict_row},
            name="spotify_tokens",
            open=True,
        )
        with self._connection() as connection:
            connection.execute(_SCHEMA)

    def close(self) -> None:
        """Shut the pool down (application shutdown, test teardown)."""
        self._pool.close()

    async def get(self, session_id: str) -> TokenBundle | None:
        """Return the stored bundle for ``session_id``, or ``None``."""
        return await asyncio.to_thread(self._get, session_id)

    async def set(self, session_id: str, bundle: TokenBundle) -> None:
        """Store or refresh the bundle for ``session_id``."""
        await asyncio.to_thread(self._set, session_id, bundle)

    async def delete(self, session_id: str) -> None:
        """Forget the tokens bound to ``session_id`` (logout)."""
        await asyncio.to_thread(self._delete, session_id)

    # ------------------------------------------------------------- internals

    def _get(self, session_id: str) -> TokenBundle | None:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT access_token, refresh_token, expires_at, scope
                FROM spotify_tokens WHERE session_id = %s
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return TokenBundle(
            access_token=str(row["access_token"]),
            refresh_token=str(row["refresh_token"]),
            expires_at=float(row["expires_at"]),
            scope=str(row["scope"]),
        )

    def _set(self, session_id: str, bundle: TokenBundle) -> None:
        with self._connection() as connection:
            connection.execute(
                _UPSERT,
                {
                    "session_id": session_id,
                    "access_token": bundle.access_token,
                    "refresh_token": bundle.refresh_token,
                    "expires_at": bundle.expires_at,
                    "scope": bundle.scope,
                },
            )

    def _delete(self, session_id: str) -> None:
        with self._connection() as connection:
            connection.execute("DELETE FROM spotify_tokens WHERE session_id = %s", (session_id,))

    @contextmanager
    def _connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        """Yield a pooled connection: commit/rollback follow the block."""
        with self._pool.connection() as connection:
            yield connection


__all__ = ["SqlTokenStore"]
