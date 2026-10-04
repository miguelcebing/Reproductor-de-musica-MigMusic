"""Tests for the lyrics use cases (own source first, then LRCLIB)."""

from __future__ import annotations

from typing import Any

import pytest

from migmusic.application.services.lyrics_service import LyricsService
from migmusic.core.exceptions import ValidationError
from migmusic.domain import AudioSourceType, Song
from migmusic.domain.entities.lyrics import Lyrics
from migmusic.domain.ports.lyrics_provider import LyricsProvider


class StubProvider(LyricsProvider):
    """Records calls and returns a configurable result or raises."""

    def __init__(self, result: Lyrics | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.calls: list[dict[str, Any]] = []

    async def find(self, *, title: str, artist: str, duration: float = 0.0) -> Lyrics | None:
        self.calls.append({"title": title, "artist": artist, "duration": duration})
        if self.error is not None:
            raise self.error
        return self.result


class StubMusicProvider:
    """Stand-in for the YouTube provider's ``get_lyrics``."""

    def __init__(self, text: str | None = None, error: Exception | None = None) -> None:
        self.text = text
        self.error = error
        self.calls = 0

    async def get_lyrics(self, song: Song) -> str | None:
        self.calls += 1
        if self.error is not None:
            raise self.error
        return self.text


def make_song(**overrides: Any) -> Song:
    values: dict[str, Any] = {
        "id": "abc123",
        "title": "Song",
        "artist": "Artist",
        "source": AudioSourceType.YOUTUBE,
        "duration": 200.0,
    }
    values.update(overrides)
    return Song(**values)


@pytest.mark.asyncio
async def test_uses_the_own_source_before_the_generic_provider() -> None:
    youtube = StubMusicProvider(text="from youtube")
    generic = StubProvider(Lyrics(text="from lrclib", source="lrclib"))
    service = LyricsService(generic, {AudioSourceType.YOUTUBE: youtube})

    result = await service.lyrics_for(make_song())

    assert result is not None
    assert result.text == "from youtube"
    assert result.source == "youtube"
    assert generic.calls == []


@pytest.mark.asyncio
async def test_falls_back_to_lrclib_when_own_source_has_none() -> None:
    youtube = StubMusicProvider(text=None)
    generic = StubProvider(Lyrics(text="from lrclib", source="lrclib"))
    service = LyricsService(generic, {AudioSourceType.YOUTUBE: youtube})

    result = await service.lyrics_for(make_song())

    assert result is not None
    assert result.text == "from lrclib"
    assert generic.calls[0]["title"] == "Song"


@pytest.mark.asyncio
async def test_spotify_tracks_go_straight_to_lrclib() -> None:
    generic = StubProvider(Lyrics(text="spotify lyrics", source="lrclib"))
    service = LyricsService(generic, {})

    result = await service.lyrics_for(make_song(source=AudioSourceType.SPOTIFY))

    assert result is not None
    assert result.text == "spotify lyrics"


@pytest.mark.asyncio
async def test_a_provider_failure_is_a_miss_not_an_error() -> None:
    generic = StubProvider(error=RuntimeError("boom"))
    service = LyricsService(generic, {})

    assert await service.lyrics_for(make_song(source=AudioSourceType.LOCAL)) is None


@pytest.mark.asyncio
async def test_misses_are_cached_so_they_are_not_asked_twice() -> None:
    generic = StubProvider(Lyrics(text="once", source="lrclib"))
    service = LyricsService(generic, {})
    song = make_song(source=AudioSourceType.LOCAL)

    first = await service.lyrics_for(song)
    second = await service.lyrics_for(song)

    assert first is not None and second is not None
    assert len(generic.calls) == 1


@pytest.mark.asyncio
async def test_empty_lyrics_object_is_rejected_by_the_entity() -> None:
    with pytest.raises(ValidationError):
        Lyrics(text="   ", source="lrclib")


def test_entity_str_credits_the_source() -> None:
    assert str(Lyrics(text="La la la " + "x" * 40, source="lrclib")).startswith("lrclib:La la la")
