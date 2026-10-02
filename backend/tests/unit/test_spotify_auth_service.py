"""Tests for the Spotify auth use cases (session, refresh, logout)."""

from __future__ import annotations

import asyncio
import time

import httpx
import pytest

from migmusic.application.services.spotify_auth_service import (
    SpotifyAuthError,
    SpotifyAuthService,
)
from migmusic.core import SpotifyConfig
from migmusic.domain.ports.token_store import TokenBundle, TokenStore
from migmusic.infrastructure.security.session_token_store import InMemoryTokenStore
from migmusic.infrastructure.spotify.spotify_oauth import SpotifyOAuth

CONFIG = SpotifyConfig(
    client_id="client-123",
    client_secret="secret-456",
    redirect_uri="http://127.0.0.1:5173/callback",
    scopes="streaming",
)


def _token_payload(access_token: str = "at-1", refresh_token: str = "rt-1") -> dict[str, str]:
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": "3600",
        "refresh_token": refresh_token,
        "scope": "streaming",
    }


def _service(store: TokenStore, payload: dict[str, str] | None = None) -> SpotifyAuthService:
    body = payload or _token_payload()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=body)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return SpotifyAuthService(SpotifyOAuth(CONFIG), store, client)


def test_callback_rejects_mismatched_state() -> None:
    """A state that does not match the cookie aborts the exchange (CSRF)."""
    service = _service(InMemoryTokenStore())

    async def run() -> None:
        with pytest.raises(SpotifyAuthError):
            await service.handle_callback(
                code="code-1",
                state="forged-state",
                expected_state="real-state",
                code_verifier="verifier",
                session_id="session-1",
            )

    asyncio.run(run())


def test_callback_persists_tokens_for_the_session() -> None:
    """A successful exchange makes the session authenticated."""
    store = InMemoryTokenStore()
    service = _service(store)

    async def run() -> None:
        await service.handle_callback(
            code="code-1",
            state="state-1",
            expected_state="state-1",
            code_verifier="verifier",
            session_id="session-1",
        )
        assert await service.is_authenticated("session-1") is True
        assert (await store.get("session-1")) is not None

    asyncio.run(run())


def test_valid_token_returns_fresh_token_without_refreshing() -> None:
    """Inside the safety margin the stored access token is reused as-is."""
    store = InMemoryTokenStore()
    service = _service(store)

    async def run() -> None:
        await store.set(
            "session-1",
            TokenBundle(
                access_token="at-fresh",
                refresh_token="rt-1",
                expires_at=time.time() + 3600,
                scope="streaming",
            ),
        )
        token = await service.valid_access_token("session-1")

        assert token is not None
        assert token.access_token == "at-fresh"
        assert token.expires_in > 3000

    asyncio.run(run())


def test_valid_token_refreshes_when_close_to_expiry() -> None:
    """Inside the refresh margin the backend silently gets a new token."""
    store = InMemoryTokenStore()
    service = _service(store, _token_payload(access_token="at-refreshed", refresh_token="rt-2"))

    async def run() -> None:
        await store.set(
            "session-1",
            TokenBundle(
                access_token="at-stale",
                refresh_token="rt-1",
                expires_at=time.time() + 10,  # < 60 s margin
                scope="streaming",
            ),
        )
        token = await service.valid_access_token("session-1")

        assert token is not None
        assert token.access_token == "at-refreshed"
        bundle = await store.get("session-1")
        assert bundle is not None and bundle.refresh_token == "rt-2"

    asyncio.run(run())


def test_failed_refresh_forgets_the_session() -> None:
    """A revoked session returns ``None`` so the UI can ask to reconnect."""
    store = InMemoryTokenStore()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = SpotifyAuthService(SpotifyOAuth(CONFIG), store, client)

    async def run() -> None:
        await store.set(
            "session-1",
            TokenBundle(
                access_token="at-stale",
                refresh_token="rt-revoked",
                expires_at=time.time() + 1,
                scope="streaming",
            ),
        )
        token = await service.valid_access_token("session-1")

        assert token is None
        assert await store.get("session-1") is None

    asyncio.run(run())


def test_transient_refresh_failure_keeps_the_session() -> None:
    """A 5xx from Spotify must not throw the refresh token away."""
    store = InMemoryTokenStore()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "temporarily_unavailable"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = SpotifyAuthService(SpotifyOAuth(CONFIG), store, client)

    async def run() -> None:
        await store.set(
            "session-1",
            TokenBundle(
                access_token="at-stale",
                refresh_token="rt-1",
                expires_at=time.time() + 1,
                scope="streaming",
            ),
        )
        token = await service.valid_access_token("session-1")

        assert token is None
        bundle = await store.get("session-1")
        assert bundle is not None and bundle.refresh_token == "rt-1"

    asyncio.run(run())


def test_malformed_refresh_response_keeps_the_session() -> None:
    """A payload we cannot parse also leaves the stored bundle untouched."""
    store = InMemoryTokenStore()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"token_type": "Bearer"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = SpotifyAuthService(SpotifyOAuth(CONFIG), store, client)

    async def run() -> None:
        await store.set(
            "session-1",
            TokenBundle(
                access_token="at-stale",
                refresh_token="rt-1",
                expires_at=time.time() + 1,
                scope="streaming",
            ),
        )
        token = await service.valid_access_token("session-1")

        assert token is None
        bundle = await store.get("session-1")
        assert bundle is not None and bundle.refresh_token == "rt-1"

    asyncio.run(run())


def test_valid_token_without_session_is_none() -> None:
    """An anonymous visitor simply has no token."""
    service = _service(InMemoryTokenStore())

    async def run() -> None:
        assert await service.valid_access_token("unknown") is None
        assert await service.is_authenticated("unknown") is False

    asyncio.run(run())


def test_logout_deletes_the_stored_tokens() -> None:
    """Logging out revokes the server-side copy of the tokens."""
    store = InMemoryTokenStore()
    service = _service(store)

    async def run() -> None:
        await store.set(
            "session-1",
            TokenBundle(
                access_token="at",
                refresh_token="rt",
                expires_at=time.time() + 3600,
                scope="streaming",
            ),
        )
        await service.logout("session-1")

        assert await store.get("session-1") is None

    asyncio.run(run())


def test_force_refresh_renews_a_token_spotify_rejected() -> None:
    """Even inside the safety margin a rejected token can be forced to refresh."""
    store = InMemoryTokenStore()
    service = _service(store, _token_payload(access_token="at-new", refresh_token="rt-2"))

    async def run() -> None:
        await store.set(
            "session-1",
            TokenBundle(
                access_token="at-rejected",
                refresh_token="rt-1",
                expires_at=time.time() + 3600,  # clock says it is still valid
                scope="streaming",
            ),
        )
        token = await service.force_refresh("session-1")

        assert token == "at-new"
        bundle = await store.get("session-1")
        assert bundle is not None
        assert bundle.access_token == "at-new"
        assert bundle.refresh_token == "rt-2"

    asyncio.run(run())


def test_force_refresh_without_a_session_returns_none() -> None:
    """An unknown session simply has nothing to refresh."""
    service = _service(InMemoryTokenStore())

    async def run() -> None:
        assert await service.force_refresh("unknown") is None

    asyncio.run(run())


def test_force_refresh_forgets_a_revoked_session() -> None:
    """``invalid_grant`` still deletes the bundle so the UI reconnects."""
    store = InMemoryTokenStore()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    service = SpotifyAuthService(SpotifyOAuth(CONFIG), store, client)

    async def run() -> None:
        await store.set(
            "session-1",
            TokenBundle(
                access_token="at-stale",
                refresh_token="rt-revoked",
                expires_at=time.time() + 3600,
                scope="streaming",
            ),
        )
        token = await service.force_refresh("session-1")

        assert token is None
        assert await store.get("session-1") is None

    asyncio.run(run())


def test_token_store_locks_concurrent_writes() -> None:
    """The in-memory store serialises writes so sessions never interleave."""
    store = InMemoryTokenStore()

    async def run() -> None:
        bundle = TokenBundle(
            access_token="at",
            refresh_token="rt",
            expires_at=time.time() + 3600,
            scope="streaming",
        )
        await asyncio.gather(*(store.set(f"session-{i}", bundle) for i in range(5)))
        assert await store.get("session-3") is not None
        await store.delete("session-3")
        assert await store.get("session-3") is None

    asyncio.run(run())
