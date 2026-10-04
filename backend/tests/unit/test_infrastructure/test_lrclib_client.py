"""Tests for the LRCLIB adapter (stubbed HTTP transport)."""

from __future__ import annotations

from typing import Any

import httpx
import pytest

from migmusic.infrastructure.lyrics import LrclibClient, LrclibError


def make_client(handler: Any) -> LrclibClient:
    transport = httpx.MockTransport(handler)
    return LrclibClient(httpx.AsyncClient(transport=transport))


@pytest.mark.asyncio
async def test_returns_plain_lyrics_and_sends_the_match_params() -> None:
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"plainLyrics": "Hello\nWorld", "syncedLyrics": None})

    lyrics = await make_client(handler).find(title="Song", artist="Artist", duration=200.4)

    assert lyrics is not None
    assert lyrics.text == "Hello\nWorld"
    assert lyrics.source == "lrclib"
    assert seen["params"] == {"track_name": "Song", "artist_name": "Artist", "duration": "200"}


@pytest.mark.asyncio
async def test_strips_lrc_timestamps_when_only_synced_lyrics_exist() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, json={"plainLyrics": None, "syncedLyrics": "[00:12.3] One\n[00:15.0] Two"}
        )

    lyrics = await make_client(handler).find(title="Song", artist="Artist")

    assert lyrics is not None
    assert lyrics.text == "One\nTwo"
    assert lyrics.synced is True


@pytest.mark.asyncio
async def test_a_404_is_a_miss_not_an_error() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"message": "not found"})

    assert await make_client(handler).find(title="Song", artist="Artist") is None


@pytest.mark.asyncio
async def test_a_server_error_surfaces_as_an_upstream_failure() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="down")

    with pytest.raises(LrclibError):
        await make_client(handler).find(title="Song", artist="Artist")


@pytest.mark.asyncio
async def test_a_timeout_surfaces_as_a_gateway_timeout() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("slow")

    with pytest.raises(LrclibError) as error:
        await make_client(handler).find(title="Song", artist="Artist")

    assert error.value.status_code == 504
