"""LRCLIB adapter: keyless lyrics for tracks whose own source has none.

LRCLIB (https://lrclib.net) is a free, open lyrics database that matches by
title and artist and needs no credentials. It covers Spotify and local tracks;
YouTube Music answers from its own source first (see ``LyricsService``).

A blank result is a *miss*, not an error: the caller caches ``None`` and the
endpoint answers ``204`` so playback is never interrupted by missing lyrics.
"""

from __future__ import annotations

from typing import Any

import httpx

from migmusic.core import get_logger
from migmusic.domain.entities.lyrics import Lyrics
from migmusic.domain.ports.lyrics_provider import LyricsProvider
from migmusic.infrastructure.lyrics.errors import LrclibError

logger = get_logger(__name__)

_BASE_URL = "https://lrclib.net/api"
# A lyrics service must never hold a request hostage; the endpoint is already
# rate limited, so failing fast keeps the rest of the app responsive.
_TIMEOUT_SECONDS = 8.0
# LRCLIB has no notion of a "best" hit; the exact-match endpoint either finds
# the track or 404s, which keeps results predictable and cacheable.
_NOT_FOUND = 404


class LrclibClient(LyricsProvider):
    """``LyricsProvider`` backed by the keyless LRCLIB HTTP API."""

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        *,
        base_url: str = _BASE_URL,
        timeout: float = _TIMEOUT_SECONDS,
    ) -> None:
        self._http = http_client
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    async def find(self, *, title: str, artist: str, duration: float = 0.0) -> Lyrics | None:
        """Look up ``title`` by ``artist``; ``None`` when LRCLIB has no match."""
        params: dict[str, str] = {"track_name": title.strip()}
        if artist.strip():
            params["artist_name"] = artist.strip()
        if duration > 0:
            # Integer seconds: LRCLIB uses it to disambiguate and rejects floats.
            params["duration"] = str(round(duration))

        try:
            response = await self._http.get(
                f"{self._base_url}/get", params=params, timeout=self._timeout
            )
        except httpx.TimeoutException as exc:
            raise LrclibError("LRCLIB timed out", status_code=504) from exc
        except httpx.HTTPError as exc:
            raise LrclibError("LRCLIB request failed") from exc

        if response.status_code == _NOT_FOUND:
            return None
        if response.status_code >= 400:
            # A 5xx or a 4xx other than "not found" is an upstream failure, not
            # a miss: let the endpoint answer 502/504 instead of a silent 204.
            raise LrclibError(
                f"LRCLIB answered {response.status_code}",
                status_code=response.status_code if response.status_code < 600 else 502,
            )

        return _to_lyrics(response.json())


def _to_lyrics(payload: Any) -> Lyrics | None:
    """Map an LRCLIB payload to the domain value object (plain text preferred)."""
    if not isinstance(payload, dict):
        return None
    plain = payload.get("plainLyrics")
    synced = payload.get("syncedLyrics")
    text = _clean(plain) or _strip_timestamps(synced)
    if not text:
        return None
    return Lyrics(text=text, source="lrclib", synced=bool(synced and not plain))


def _clean(value: Any) -> str | None:
    """Trim a payload string, returning ``None`` when it is blank."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def _strip_timestamps(value: Any) -> str | None:
    """Drop ``[mm:ss.xx]`` LRC markers, keeping the readable lines."""
    if not isinstance(value, str):
        return None
    lines: list[str] = []
    for raw in value.splitlines():
        line = raw.strip()
        while line.startswith("["):
            end = line.find("]")
            if end == -1:
                break
            line = line[end + 1 :].strip()
        if line:
            lines.append(line)
    return "\n".join(lines) or None


__all__ = ["LrclibClient"]
