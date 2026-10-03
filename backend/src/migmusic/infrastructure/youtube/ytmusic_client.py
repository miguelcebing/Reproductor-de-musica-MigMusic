"""Thin, cached wrapper over a single ``YTMusic`` instance.

``ytmusicapi`` is synchronous and builds its own ``requests`` session; calling
it from the event loop would block every other request. One instance is created
per process (no OAuth, no cookies: see the task rules) and every call runs in a
worker thread via ``asyncio.to_thread``.

The library is unofficial and may break on Google's side; it is isolated here
so the fix never reaches the domain or the API layer.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar

from migmusic.core import get_logger
from migmusic.infrastructure.cache import TtlCache
from migmusic.infrastructure.youtube.errors import YouTubeMusicError

logger = get_logger(__name__)

T = TypeVar("T")

# Searches repeat constantly while typing; lyrics are stable for a long time.
_SEARCH_TTL_SECONDS = 300.0
_LYRICS_TTL_SECONDS = 60 * 60 * 24


class YtMusicClient:
    """Keyless YouTube Music client: search, watch playlist and lyrics."""

    def __init__(self, *, language: str = "en", timeout: float = 8.0) -> None:
        """Create the single ``YTMusic`` instance (or fail fast at import use).

        Args:
            language: YouTube Music UI/metadata language (``en``, ``es``, ...).
            timeout: Seconds after which a call is abandoned (unofficial API).
        """
        self._language = language
        self._timeout = timeout
        self._ytmusic: Any | None = None
        self._search_cache: TtlCache[str, list[dict[str, Any]]] = TtlCache(
            ttl=_SEARCH_TTL_SECONDS, max_size=256
        )
        self._lyrics_cache: TtlCache[str, str | None] = TtlCache(
            ttl=_LYRICS_TTL_SECONDS, max_size=256
        )

    # ------------------------------------------------------------- public API

    async def search(self, query: str, *, limit: int) -> list[dict[str, Any]]:
        """Search songs, mapped to plain dicts; empty list when nothing matches."""
        key = f"{query.strip().casefold()}::{limit}"
        cached = self._search_cache.get(key)
        if cached is not None:
            return cached
        results = await self._call(
            lambda yt: yt.search(query, filter="songs", limit=max(1, limit)),
            operation_name="search",
        )
        songs = [item for item in results if isinstance(item, dict) and item.get("videoId")]
        self._search_cache.set(key, songs)
        return songs

    async def get_song(self, video_id: str) -> dict[str, Any] | None:
        """Return one song's metadata (``videoDetails``), or ``None``."""
        data = await self._call(lambda yt: yt.get_song(video_id), operation_name="get_song")
        if not isinstance(data, dict):
            return None
        details = data.get("videoDetails")
        return details if isinstance(details, dict) else None

    async def get_lyrics(self, video_id: str) -> str | None:
        """Return the plain lyrics for ``video_id``, or ``None`` when absent.

        The browse id is resolved through the watch playlist first, exactly as
        the library documents. Results (including misses) are cached.
        """
        cached = self._lyrics_cache.get(video_id)
        if cached is not None:
            return cached
        browse_id = await self._call(
            lambda yt: yt.get_watch_playlist(video_id, limit=1).get("lyrics"),
            operation_name="get_watch_playlist",
        )
        if not browse_id:
            self._lyrics_cache.set(video_id, None)
            return None
        payload = await self._call(
            lambda yt: yt.get_lyrics(browse_id), operation_name="get_lyrics"
        )
        lyrics = payload.get("lyrics") if isinstance(payload, dict) else None
        text = lyrics.strip() if isinstance(lyrics, str) and lyrics.strip() else None
        self._lyrics_cache.set(video_id, text)
        return text

    # ------------------------------------------------------------- internals

    def _get_ytmusic(self) -> Any:
        """Build the shared ``YTMusic`` instance on first use (lazy import)."""
        if self._ytmusic is None:
            try:
                from ytmusicapi import YTMusic
            except ImportError as exc:  # pragma: no cover - dependency is pinned
                raise YouTubeMusicError("ytmusicapi is not installed") from exc
            self._ytmusic = YTMusic(language=self._language)
            logger.info("ytmusic_client_ready", extra={"language": self._language})
        return self._ytmusic

    async def _call(self, operation: Callable[[Any], T], *, operation_name: str) -> T:
        """Run a synchronous library call in a worker thread with a timeout."""

        def run() -> T:
            return operation(self._get_ytmusic())

        try:
            return await asyncio.wait_for(asyncio.to_thread(run), timeout=self._timeout)
        except TimeoutError as exc:
            raise YouTubeMusicError(
                f"YouTube Music timed out during {operation_name}", status_code=504
            ) from exc
        except YouTubeMusicError:
            raise
        except Exception as exc:
            logger.warning("ytmusic_call_failed [%s]: %s", operation_name, exc)
            raise YouTubeMusicError(f"YouTube Music failed during {operation_name}") from exc


__all__ = ["YtMusicClient"]
