"""Contract tests for the PostgreSQL token store (`SKILL3`, `HANDOFF`).

The regression these guard against: an in-memory store dies with the process,
so every Render restart silently unlinked Spotify. The suite runs against a
real PostgreSQL (``TEST_DATABASE_URL`` or the embedded ``pgserver``), exactly
like the playlist repository contract tests.
"""

from __future__ import annotations

import time

import psycopg
import pytest
from postgres_dsn import DSN as _DSN

from migmusic.domain.ports.token_store import TokenBundle
from migmusic.infrastructure.security.sql_token_store import SqlTokenStore

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _DSN, reason="no PostgreSQL available (set TEST_DATABASE_URL)"),
]


@pytest.fixture
def token_store() -> SqlTokenStore:
    """Fresh schema rows per test, then an adapter over them."""
    store = SqlTokenStore(_DSN)
    with psycopg.connect(_DSN) as connection:
        connection.execute("TRUNCATE spotify_tokens")
    return store


def _bundle(*, access_token: str = "access-token-1") -> TokenBundle:
    return TokenBundle(
        access_token=access_token,
        refresh_token="refresh-token-1",
        expires_at=time.time() + 3600,
        scope="streaming user-read-email",
    )


async def test_set_then_get_round_trip(token_store: SqlTokenStore) -> None:
    bundle = _bundle()

    await token_store.set("session-1", bundle)

    assert await token_store.get("session-1") == bundle


async def test_get_for_an_unknown_session_returns_none(
    token_store: SqlTokenStore,
) -> None:
    assert await token_store.get("nope") is None


async def test_set_refreshes_an_existing_session(token_store: SqlTokenStore) -> None:
    await token_store.set("session-1", _bundle(access_token="first"))
    refreshed = _bundle(access_token="second")

    await token_store.set("session-1", refreshed)

    assert await token_store.get("session-1") == refreshed


async def test_delete_forgets_the_session(token_store: SqlTokenStore) -> None:
    await token_store.set("session-1", _bundle())

    await token_store.delete("session-1")

    assert await token_store.get("session-1") is None
    await token_store.delete("missing")  # idempotent


async def test_tokens_survive_a_new_process(token_store: SqlTokenStore) -> None:
    """The whole point: a restart must not force the user to re-link Spotify."""
    bundle = _bundle()
    await token_store.set("session-1", bundle)

    restarted = SqlTokenStore(_DSN)

    assert await restarted.get("session-1") == bundle


def test_empty_dsn_is_rejected() -> None:
    with pytest.raises(ValueError, match="DSN"):
        SqlTokenStore("   ")
