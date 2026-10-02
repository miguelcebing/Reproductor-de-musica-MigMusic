"""Tests for the self-ping loop that keeps the free-tier instance awake."""

from __future__ import annotations

import asyncio

import httpx
import pytest

from migmusic.infrastructure.keep_alive import keep_alive_loop, keep_alive_url, make_pinger


def test_keep_alive_url_points_at_the_public_health_endpoint() -> None:
    """The ping must travel through the router, so it uses the public URL."""
    assert keep_alive_url("https://api.example.com/") == "https://api.example.com/api/health"
    assert keep_alive_url("https://api.example.com") == "https://api.example.com/api/health"


async def test_pinger_gets_the_public_health_url() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={"status": "ok"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        await make_pinger(client, "https://api.example.com")()

    assert seen == ["https://api.example.com/api/health"]


async def test_pinger_surfaces_a_failed_health_check() -> None:
    """A 5xx from our own endpoint must reach the loop, which swallows it."""
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    async with httpx.AsyncClient(transport=transport) as client:
        ping = make_pinger(client, "https://api.example.com")

        with pytest.raises(httpx.HTTPStatusError):
            await ping()


async def test_loop_pings_on_schedule_and_survives_failures() -> None:
    """Every interval triggers a ping; a failed ping never stops the loop."""
    pings: list[int] = []
    sleeps: list[float] = []

    async def ping() -> None:
        pings.append(len(pings) + 1)
        if len(pings) == 1:
            raise RuntimeError("first ping fails")

    async def sleep(seconds: float) -> None:
        sleeps.append(seconds)
        if len(sleeps) > 3:
            raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await keep_alive_loop(ping, interval_s=600, sleep=sleep)

    assert sleeps == [600.0, 600.0, 600.0, 600.0]
    assert pings == [1, 2, 3]  # the first failure did not end the loop
