"""Tests for the YouTube Music -> domain song mapping."""

from __future__ import annotations

import asyncio
from typing import Any

from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.infrastructure.youtube import YouTubeMusicProvider, YtMusicClient


class FakeYtMusicClient(YtMusicClient):
    """Client double that returns canned payloads instead of hitting the API."""

    def __init__(
        self,
        *,
        search: list[dict[str, Any]] | None = None,
        song: dict[str, Any] | None = None,
        lyrics: str | None = None,
    ) -> None:
        super().__init__()
        self._search = search or []
        self._song = song
        self._lyrics = lyrics

    async def search(self, query: str, *, limit: int) -> list[dict[str, Any]]:
        return self._search

    async def get_song(self, video_id: str) -> dict[str, Any] | None:
        return self._song

    async def get_lyrics(self, video_id: str) -> str | None:
        return self._lyrics


def _result(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "videoId": "vid1",
        "title": "Wonderwall",
        "duration_seconds": 259,
        "artists": [{"name": "Oasis"}],
        "album": {"name": "(What's The Story) Morning Glory?"},
        "thumbnails": [
            {"url": "https://img/60.jpg", "width": 60, "height": 60},
            {"url": "https://img/226.jpg", "width": 226, "height": 226},
        ],
    }
    base.update(overrides)
    return base


def test_search_maps_to_a_domain_song() -> None:
    provider = YouTubeMusicProvider(FakeYtMusicClient(search=[_result()]))

    songs = asyncio.run(provider.search_tracks("oasis", limit=10))

    assert len(songs) == 1
    song = songs[0]
    assert song.id == "vid1"
    assert song.title == "Wonderwall"
    assert song.artist == "Oasis"
    assert song.source == AudioSourceType.YOUTUBE
    assert song.duration == 259
    assert song.album == "(What's The Story) Morning Glory?"
    # The mid-size thumbnail wins over the tiny one.
    assert song.artwork_url == "https://img/226.jpg"
    assert song.external_url == "https://music.youtube.com/watch?v=vid1"


def test_search_skips_entries_without_a_video_id_or_title() -> None:
    provider = YouTubeMusicProvider(
        FakeYtMusicClient(
            search=[
                _result(),
                {"title": "No id"},
                _result(videoId="x", title="   "),
            ]
        )
    )

    songs = asyncio.run(provider.search_tracks("q"))

    assert [song.id for song in songs] == ["vid1"]


def test_get_track_maps_video_details() -> None:
    provider = YouTubeMusicProvider(
        FakeYtMusicClient(
            song={"title": "Wonderwall", "author": "Oasis", "lengthSeconds": "259"}
        )
    )

    song = asyncio.run(provider.get_track("vid1"))

    assert song is not None
    assert song.id == "vid1"
    assert song.artist == "Oasis"
    assert song.duration == 259


def test_get_track_returns_none_without_details() -> None:
    provider = YouTubeMusicProvider(FakeYtMusicClient())

    assert asyncio.run(provider.get_track("missing")) is None


def test_get_lyrics_delegates_to_the_client() -> None:
    provider = YouTubeMusicProvider(FakeYtMusicClient(lyrics="Today is gonna be the day"))

    from migmusic.domain.entities.song import Song

    track = Song(id="vid1", title="Wonderwall", artist="Oasis", source=AudioSourceType.YOUTUBE)

    assert asyncio.run(provider.get_lyrics(track)) == "Today is gonna be the day"
