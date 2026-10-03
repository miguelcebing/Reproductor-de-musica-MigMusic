"""Lyrics use cases: resolve a song's lyrics from the best available source.

Strategy (first hit wins):

1. the track's own :class:`MusicProvider` when it can serve lyrics (YouTube
   Music via ``get_watch_playlist`` + ``get_lyrics``);
2. the generic :class:`LyricsProvider` (LRCLIB), matched by title and artist,
   which covers Spotify and local tracks that carry no lyrics of their own.

Results — including misses — are cached with a TTL so retyping or replaying a
song does not hit the network again.
"""

from __future__ import annotations

from migmusic.core import get_logger
from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.domain.entities.lyrics import Lyrics
from migmusic.domain.entities.song import Song
from migmusic.domain.ports.lyrics_provider import LyricsProvider
from migmusic.infrastructure.cache import TtlCache

logger = get_logger(__name__)

# Lyrics change rarely; a day keeps the cache useful without pinning stale data.
_LYRICS_TTL_SECONDS = 60 * 60 * 24
_LYRICS_CACHE_SIZE = 256


def _cache_key(song: Song) -> str:
    """Stable cache key: the source track id when present, else title+artist."""
    if song.id:
        return f"{song.source.value}:{song.id}"
    return f"{song.source.value}:{song.title.casefold()}:{song.artist.casefold()}"


class LyricsService:
    """Resolve lyrics for a :class:`Song` from the configured sources."""

    def __init__(
        self,
        provider: LyricsProvider | None,
        music_providers: dict[AudioSourceType, object] | None = None,
    ) -> None:
        self._provider = provider
        self._music_providers = music_providers or {}
        self._cache: TtlCache[str, Lyrics | None] = TtlCache(
            ttl=_LYRICS_TTL_SECONDS, max_size=_LYRICS_CACHE_SIZE
        )

    def register_music_provider(self, source: AudioSourceType, provider: object) -> None:
        """Attach a source adapter that may serve lyrics of its own."""
        self._music_providers[source] = provider

    async def lyrics_for(self, song: Song) -> Lyrics | None:
        """Return the lyrics for ``song`` or ``None``; misses are cached too."""
        key = _cache_key(song)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        lyrics = await self._resolve(song)
        self._cache.set(key, lyrics)
        return lyrics

    def cache_clear(self) -> None:
        """Drop every cached answer (tests)."""
        self._cache.clear()

    async def _resolve(self, song: Song) -> Lyrics | None:
        """Try the song's own source first, then the generic provider."""
        own = await self._from_own_source(song)
        if own is not None:
            return own
        if self._provider is None:
            return None
        try:
            return await self._provider.find(
                title=song.title, artist=song.artist, duration=song.duration
            )
        except Exception as exc:  # external adapter: a miss must not break playback
            logger.warning("lyrics_provider_failed source=%s error=%s", song.source.value, exc)
            return None

    async def _from_own_source(self, song: Song) -> Lyrics | None:
        """Ask the track's own provider (YouTube Music) for lyrics, if it can."""
        provider = self._music_providers.get(song.source)
        if provider is None:
            return None
        get_lyrics = getattr(provider, "get_lyrics", None)
        if get_lyrics is None:
            return None
        try:
            text = await get_lyrics(song)
        except Exception as exc:  # provider-specific failures fall back to LRCLIB
            logger.warning("lyrics_own_source_failed source=%s error=%s", song.source.value, exc)
            return None
        if not isinstance(text, str) or not text.strip():
            return None
        return Lyrics(text=text.strip(), source="youtube", synced=False)


__all__ = ["LyricsService"]
