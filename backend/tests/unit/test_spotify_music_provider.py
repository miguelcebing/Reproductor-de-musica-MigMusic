"""Tests for the Spotify -> domain song mapping."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.infrastructure.spotify.spotify_client import SpotifyApiClient
from migmusic.infrastructure.spotify.spotify_music_provider import SpotifyMusicProvider


def _track(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": "abc123",
        "name": "Night Drive",
        "duration_ms": 215_400,
        "uri": "spotify:track:abc123",
        "artists": [{"name": "Kavinsky"}, {"name": "Lovefoxxx"}],
        "album": {
            "name": "OutRun",
            "images": [{"url": "https://i.scdn.co/image/cover"}],
        },
        "external_urls": {"spotify": "https://open.spotify.com/track/abc123"},
        "is_playable": True,
    }
    base.update(overrides)
    return base


def _provider(payload: Any) -> SpotifyMusicProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = SpotifyApiClient(httpx.AsyncClient(transport=httpx.MockTransport(handler)))
    return SpotifyMusicProvider(client)


def test_track_maps_to_a_domain_song() -> None:
    """Every Spotify field lands on the matching ``Song`` attribute."""
    provider = _provider({"tracks": {"items": [_track()]}})

    songs = asyncio.run(provider.search_tracks("token", "night"))

    assert len(songs) == 1
    song = songs[0]
    assert song.id == "abc123"
    assert song.title == "Night Drive"
    assert song.artist == "Kavinsky, Lovefoxxx"
    assert song.source == AudioSourceType.SPOTIFY
    assert song.duration == 215.4
    assert song.album == "OutRun"
    assert song.artwork_url == "https://i.scdn.co/image/cover"
    assert song.external_url == "https://open.spotify.com/track/abc123"
    assert song.available is True
    assert song.duration_label == "3:35"


def test_search_skips_unusable_entries() -> None:
    """Episodes, nulls and title-less tracks never reach the list."""
    provider = _provider(
        {
            "tracks": {
                "items": [
                    _track(),
                    None,
                    {"id": "ep1", "name": "Episode", "type": "episode"},
                    _track(id="no-title", name="   "),
                ]
            }
        }
    )

    songs = asyncio.run(provider.search_tracks("token", "q"))

    assert [song.id for song in songs] == ["abc123"]


def test_saved_tracks_unwraps_the_track_envelope() -> None:
    """``/me/tracks`` wraps each track in an ``item`` object."""
    provider = _provider({"items": [{"added_at": "2024-01-01", "track": _track()}]})

    songs = asyncio.run(provider.saved_tracks("token"))

    assert len(songs) == 1
    assert songs[0].title == "Night Drive"


def test_playlist_tracks_unwraps_its_envelope() -> None:
    """Playlist items carry the track under ``track``."""
    provider = _provider({"items": [{"track": _track()}, {"track": None}]})

    songs = asyncio.run(provider.playlist_tracks("token", "playlist-1"))

    assert len(songs) == 1


def test_unplayable_track_is_marked_unavailable() -> None:
    """Region-restricted tracks are listed but flagged, never hidden."""
    provider = _provider({"tracks": {"items": [_track(is_playable=False)]}})

    songs = asyncio.run(provider.search_tracks("token", "q"))

    assert songs[0].available is False


def test_missing_duration_and_artwork_are_tolerated() -> None:
    """Partial payloads still produce a valid song."""
    provider = _provider(
        {
            "tracks": {
                "items": [
                    {
                        "id": "x1",
                        "name": "Sparse",
                        "artists": [{"name": "A"}],
                        "album": None,
                    }
                ]
            }
        }
    )

    songs = asyncio.run(provider.search_tracks("token", "q"))

    assert songs[0].duration == 0.0
    assert songs[0].artwork_url is None
    assert songs[0].album is None


def test_search_handles_a_malformed_envelope() -> None:
    """A weird upstream body yields an empty list instead of a crash."""
    provider = _provider({"tracks": {"items": "not-a-list"}})

    assert asyncio.run(provider.search_tracks("token", "q")) == []
