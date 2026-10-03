"""Synchronous-in-shape async client for the Spotify Web API.

Every call takes an ``access_token`` because tokens are session-scoped and
refreshed by the application layer; the client itself stays stateless.

Failure policy (``SKILL3``):
- timeout 10 s per attempt,
- one retry with backoff on 429/5xx, honouring ``Retry-After`` up to 3 s,
- 401 replayed once with a freshly refreshed token before it is raised as
  :class:`SpotifyAuthError` so the caller can reconnect,
- everything else raised as :class:`SpotifyApiError` with the upstream status.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextvars import ContextVar
from typing import Any

import httpx

from migmusic.application.dto.spotify import SpotifyPlaylistSummary
from migmusic.infrastructure.spotify.errors import (
    SpotifyApiError,
    SpotifyAuthError,
    SpotifyRateLimitError,
)

_RETRYABLE_STATUS = {429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 2
_MAX_RETRY_AFTER = 3.0

TokenRefresher = Callable[[], Awaitable[str | None]]

# Set per request by ``require_spotify_token``; consulted exactly once when
# Spotify answers 401 so the call can be replayed with a fresh token.
token_refresher: ContextVar[TokenRefresher | None] = ContextVar(
    "spotify_token_refresher", default=None
)
# `/v1/search` answers 400 "Invalid limit" for anything above 10 results
# (verified against the live API on 2026-10-01 with a user token).
_SEARCH_LIMIT_MAX = 10


class SpotifyApiClient:
    """Thin wrapper over ``https://api.spotify.com/v1``."""

    API_BASE = "https://api.spotify.com/v1"

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    # --- Catalog -------------------------------------------------------------

    async def search_tracks(
        self, token: str, query: str, *, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Search tracks; returns the raw ``items`` array.

        The ask is clamped to the cap Spotify enforces on ``/search``; if the
        cap ever shrinks below it, the query is retried once with a single
        result instead of failing the whole search with a 400.
        """
        wanted = max(1, min(limit, _SEARCH_LIMIT_MAX))
        params: dict[str, Any] = {"q": query, "type": "track", "limit": wanted}
        try:
            data = await self._request("GET", "/search", token, params=params)
        except SpotifyApiError as exc:
            if wanted == 1 or exc.status_code != 400 or "Invalid limit" not in str(exc):
                raise
            params["limit"] = 1
            data = await self._request("GET", "/search", token, params=params)
        return _items(data, "tracks")

    async def track(self, token: str, track_id: str) -> dict[str, Any]:
        """Return one track by id (``GET /tracks/{id}``)."""
        return await self._request("GET", f"/tracks/{track_id}", token)

    async def saved_tracks(self, token: str, *, limit: int = 20) -> list[dict[str, Any]]:
        """Tracks saved to the user's library (``user-library-read``)."""
        data = await self._request(
            "GET",
            "/me/tracks",
            token,
            params={"limit": max(1, min(limit, 50))},
        )
        return _items(data)

    async def playlist_tracks(
        self, token: str, playlist_id: str, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Tracks of one playlist (``playlist-read-private``)."""
        data = await self._request(
            "GET",
            f"/playlists/{playlist_id}/tracks",
            token,
            params={"limit": max(1, min(limit, 100))},
        )
        return _items(data)

    async def list_playlists(self, token: str, *, limit: int = 20) -> list[SpotifyPlaylistSummary]:
        """Headers of the playlists the current user owns or follows."""
        data = await self._request(
            "GET",
            "/me/playlists",
            token,
            params={"limit": max(1, min(limit, 50))},
        )
        return [
            SpotifyPlaylistSummary(
                id=str(item["id"]),
                name=str(item.get("name") or "Untitled"),
                track_count=_playlist_track_count(item),
                artwork_url=_first_image(item.get("images")),
            )
            for item in _items(data)
            if item.get("id")
        ]

    # --- Playback (SDK backend proxy) ----------------------------------------

    async def start_playback(
        self,
        token: str,
        *,
        device_id: str | None = None,
        uris: list[str] | None = None,
        position_ms: int = 0,
    ) -> None:
        """Start/resume playback on ``device_id`` (``PUT /me/player/play``)."""
        body: dict[str, Any] = {"position_ms": max(0, position_ms)}
        if uris:
            body["uris"] = uris
        await self._request(
            "PUT",
            "/me/player/play",
            token,
            params={"device_id": device_id} if device_id else None,
            body=body,
            expect_empty=True,
        )

    async def pause_playback(self, token: str, *, device_id: str | None = None) -> None:
        """Pause playback on ``device_id``."""
        await self._request(
            "PUT",
            "/me/player/pause",
            token,
            params={"device_id": device_id} if device_id else None,
            expect_empty=True,
        )

    async def next_track(self, token: str, *, device_id: str | None = None) -> None:
        """Skip to the next track."""
        await self._request(
            "POST",
            "/me/player/next",
            token,
            params={"device_id": device_id} if device_id else None,
            expect_empty=True,
        )

    async def previous_track(self, token: str, *, device_id: str | None = None) -> None:
        """Skip to the previous track."""
        await self._request(
            "POST",
            "/me/player/previous",
            token,
            params={"device_id": device_id} if device_id else None,
            expect_empty=True,
        )

    async def seek(self, token: str, position_ms: int, *, device_id: str | None = None) -> None:
        """Seek to ``position_ms`` (clamped to 0 by the caller)."""
        await self._request(
            "PUT",
            "/me/player/seek",
            token,
            params={
                "position_ms": max(0, position_ms),
                **({"device_id": device_id} if device_id else {}),
            },
            expect_empty=True,
        )

    async def set_volume(
        self, token: str, volume_percent: int, *, device_id: str | None = None
    ) -> None:
        """Set playback volume (0-100)."""
        level = max(0, min(100, volume_percent))
        await self._request(
            "PUT",
            "/me/player/volume",
            token,
            params={"volume_percent": level, **({"device_id": device_id} if device_id else {})},
            expect_empty=True,
        )

    async def playback_state(self, token: str) -> dict[str, Any] | None:
        """Current playback object, or ``None`` when nothing is playing."""
        try:
            data = await self._request("GET", "/me/player", token)
        except SpotifyApiError as exc:
            if exc.status_code == 404:
                return None
            raise
        return data if isinstance(data, dict) else None

    # --- Plumbing -------------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        token: str,
        *,
        params: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
        expect_empty: bool = False,
    ) -> dict[str, Any]:
        url = f"{self.API_BASE}{path}"
        headers = {"authorization": f"Bearer {token}", "accept": "application/json"}

        last_error: SpotifyApiError | None = None
        auth_retried = False
        # +1: the extra pass replays the request after a token refresh.
        for attempt in range(_MAX_ATTEMPTS + 1):
            try:
                response = await self._http.request(
                    method,
                    url,
                    params=params,
                    json=body,
                    headers=headers,
                    timeout=10.0,
                )
            except httpx.TimeoutException as exc:
                last_error = SpotifyApiError("Spotify request timed out", status_code=504)
                if attempt + 1 < _MAX_ATTEMPTS:
                    await asyncio.sleep(0.2 * (attempt + 1))
                    continue
                raise last_error from exc
            except httpx.RequestError as exc:
                raise SpotifyApiError(f"Spotify unreachable: {exc}", status_code=502) from exc

            if response.status_code == 401 and not auth_retried:
                auth_retried = True
                refresh = token_refresher.get()
                renewed = await refresh() if refresh else None
                if renewed:
                    headers["authorization"] = f"Bearer {renewed}"
                    continue

            if response.status_code in _RETRYABLE_STATUS:
                last_error = self._status_error(response)
                if attempt + 1 < _MAX_ATTEMPTS:
                    await asyncio.sleep(self._retry_delay(response))
                    continue
                raise last_error

            self._raise_for_status(response)

            if expect_empty or response.status_code == 204 or not response.content:
                return {}
            try:
                payload = response.json()
            except ValueError as exc:
                raise SpotifyApiError("Spotify returned a malformed body", status_code=502) from exc
            if isinstance(payload, dict):
                return payload
            # List payloads are wrapped so callers can index into them.
            return {"items": payload}

        raise last_error if last_error else SpotifyApiError("Spotify request failed")

    @classmethod
    def _status_error(cls, response: httpx.Response) -> SpotifyApiError:
        if response.status_code == 401:
            return SpotifyAuthError("Spotify access token rejected", status_code=401)
        if response.status_code == 429:
            retry_after = _parse_retry_after(response.headers.get("retry-after"))
            return SpotifyRateLimitError(retry_after)
        if 400 <= response.status_code < 500:
            # 404 (no device) and 409 (command rejected) stay meaningful upstream.
            # The upstream message ("Invalid limit", "bad request"...) travels
            # inside the error so logs can explain it; clients only ever see
            # the generic "{service} unavailable" envelope.
            detail = cls._upstream_detail(response)
            return SpotifyApiError(
                f"Spotify answered {response.status_code}" + (f": {detail}" if detail else ""),
                status_code=response.status_code,
            )
        return SpotifyApiError("Spotify answered an upstream error", status_code=502)

    @staticmethod
    def _upstream_detail(response: httpx.Response) -> str | None:
        """Read ``error.message`` out of a Spotify error body, when present."""
        try:
            payload: Any = response.json()
        except ValueError:
            return None
        if not isinstance(payload, dict):
            return None
        error: Any = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            return message if isinstance(message, str) else None
        return error if isinstance(error, str) else None

    @classmethod
    def _raise_for_status(cls, response: httpx.Response) -> None:
        if response.is_success:
            return
        raise cls._status_error(response)

    @staticmethod
    def _retry_delay(response: httpx.Response) -> float:
        if response.status_code == 429:
            delay = float(_parse_retry_after(response.headers.get("retry-after")))
            return min(_MAX_RETRY_AFTER, delay)
        return 0.3


def _parse_retry_after(raw: str | None) -> int:
    """Parse ``Retry-After`` (seconds only; HTTP-date form is rare for Spotify)."""
    if not raw:
        return 1
    try:
        return max(1, int(raw))
    except ValueError:
        return 1


def _items(payload: dict[str, Any], key: str | None = None) -> list[dict[str, Any]]:
    """Extract the ``items`` array (optionally nested under ``key``) safely."""
    node: Any = payload if key is None else payload.get(key)
    if not isinstance(node, dict):
        return []
    raw = node.get("items")
    if not isinstance(raw, list):
        return []
    return [entry for entry in raw if isinstance(entry, dict)]


def _playlist_track_count(item: dict[str, Any]) -> int:
    """Read ``tracks.total`` defensively; Spotify sometimes sends ``null``."""
    tracks = item.get("tracks")
    if isinstance(tracks, dict):
        total = tracks.get("total")
        if isinstance(total, (int, float)):
            return int(total)
    return 0


def _first_image(images: Any) -> str | None:
    """Pick the first (largest) artwork URL from a Spotify ``images`` array."""
    if not isinstance(images, list) or not images:
        return None
    first = images[0]
    if isinstance(first, dict):
        url = first.get("url")
        if isinstance(url, str):
            return url
    return None


__all__ = ["SpotifyApiClient"]
