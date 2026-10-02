"""HTTP contract of the Spotify Web API client (limits, retries, error text)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx
import pytest

from migmusic.infrastructure.spotify.errors import SpotifyApiError, SpotifyAuthError
from migmusic.infrastructure.spotify.spotify_client import SpotifyApiClient, token_refresher

Handler = Callable[[httpx.Request], httpx.Response]


def _client(handler: Handler) -> SpotifyApiClient:
    return SpotifyApiClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)))


def test_search_clamps_the_limit_to_what_spotify_accepts() -> None:
    """`/search` rejects anything above 10 results, so the ask is clamped."""
    seen: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(int(request.url.params["limit"]))
        return httpx.Response(200, json={"tracks": {"items": []}})

    asyncio.run(_client(handler).search_tracks("token", "night", limit=50))

    assert seen == [10]


def test_search_keeps_a_limit_spotify_already_accepts() -> None:
    """A request inside the cap is forwarded untouched."""
    seen: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(int(request.url.params["limit"]))
        return httpx.Response(200, json={"tracks": {"items": []}})

    asyncio.run(_client(handler).search_tracks("token", "night", limit=7))

    assert seen == [7]


def test_search_falls_back_to_one_result_when_the_cap_shrinks() -> None:
    """A 400 "Invalid limit" retries once instead of failing the search."""
    seen: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        limit = int(request.url.params["limit"])
        seen.append(limit)
        if limit > 1:
            return httpx.Response(400, json={"error": {"status": 400, "message": "Invalid limit"}})
        return httpx.Response(
            200, json={"tracks": {"items": [{"id": "abc123", "name": "Night Drive"}]}}
        )

    songs = asyncio.run(_client(handler).search_tracks("token", "night", limit=5))

    assert seen == [5, 1]
    assert [song["id"] for song in songs] == ["abc123"]


def test_a_different_400_is_raised_without_a_second_call() -> None:
    """Only "Invalid limit" is retried; other 400s surface immediately."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(400, json={"error": {"status": 400, "message": "Invalid q"}})

    with pytest.raises(SpotifyApiError) as excinfo:
        asyncio.run(_client(handler).search_tracks("token", "night", limit=5))

    assert len(calls) == 1
    assert str(excinfo.value) == "Spotify answered 400: Invalid q"
    assert excinfo.value.status_code == 400


def test_a_body_that_is_not_json_still_produces_a_usable_error() -> None:
    """Non-JSON upstream bodies are reported without a bogus detail."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(400, text="<html>nope</html>")

    with pytest.raises(SpotifyApiError) as excinfo:
        asyncio.run(_client(handler).search_tracks("token", "night", limit=5))

    assert len(calls) == 1
    assert str(excinfo.value) == "Spotify answered 400"


def test_a_rejected_token_is_an_auth_error() -> None:
    """401 maps to ``SpotifyAuthError`` so callers can ask the user to reconnect."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": {"status": 401, "message": "expired"}})

    with pytest.raises(SpotifyAuthError):
        asyncio.run(_client(handler).search_tracks("token", "night", limit=5))


def test_a_rejected_token_is_replayed_with_a_refreshed_one() -> None:
    """One 401 refreshes the token and replays the call instead of failing."""
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers["authorization"])
        if request.headers["authorization"] == "Bearer token":
            return httpx.Response(401, json={"error": {"status": 401, "message": "expired"}})
        return httpx.Response(200, json={"tracks": {"items": []}})

    async def refresher() -> str | None:
        return "renewed"

    async def run() -> list[dict[str, object]]:
        token_refresher.set(refresher)
        try:
            return await _client(handler).search_tracks("token", "night", limit=5)
        finally:
            token_refresher.set(None)

    songs = asyncio.run(run())

    assert seen == ["Bearer token", "Bearer renewed"]
    assert songs == []


def test_a_refresh_that_fails_keeps_the_original_auth_error() -> None:
    """When no new token can be had the 401 surfaces without a second call."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401, json={"error": {"status": 401, "message": "expired"}})

    async def refresher() -> str | None:
        return None

    async def run() -> None:
        token_refresher.set(refresher)
        try:
            await _client(handler).search_tracks("token", "night", limit=5)
        finally:
            token_refresher.set(None)

    with pytest.raises(SpotifyAuthError):
        asyncio.run(run())

    assert len(calls) == 1


def test_a_second_401_is_raised_instead_of_looping() -> None:
    """The refresh replay happens at most once per request."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(401, json={"error": {"status": 401, "message": "expired"}})

    async def refresher() -> str | None:
        return "renewed"

    async def run() -> None:
        token_refresher.set(refresher)
        try:
            await _client(handler).search_tracks("token", "night", limit=5)
        finally:
            token_refresher.set(None)

    with pytest.raises(SpotifyAuthError):
        asyncio.run(run())

    assert len(calls) == 2


def test_server_errors_become_a_gateway_error() -> None:
    """5xx is retried once and then reported as an upstream failure."""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(503, text="maintenance")

    with pytest.raises(SpotifyApiError) as excinfo:
        asyncio.run(_client(handler).search_tracks("token", "night", limit=5))

    assert len(calls) == 2
    assert str(excinfo.value) == "Spotify answered an upstream error"
    assert excinfo.value.status_code == 502
