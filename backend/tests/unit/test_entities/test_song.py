"""Tests for the immutable ``Song`` value object."""

from __future__ import annotations

import dataclasses

import pytest

from migmusic.core import ValidationError
from migmusic.domain import AudioSourceType, Song


def make_song(**overrides: object) -> Song:
    """Build a valid song, overriding any field by keyword."""
    values: dict[str, object] = {
        "id": "local-1",
        "title": "Nocturne",
        "artist": "MigMusic",
        "source": AudioSourceType.LOCAL,
        "duration": 183.0,
    }
    values.update(overrides)
    return Song(**values)  # type: ignore[arg-type]


def test_song_is_valid_by_default() -> None:
    """The happy path builds a usable value object."""
    song = make_song()

    assert song.title == "Nocturne"
    assert song.source is AudioSourceType.LOCAL
    assert song.available is True
    assert song.album is None


def test_song_is_immutable() -> None:
    """Frozen dataclass: a value object cannot be edited in place."""
    song = make_song()

    with pytest.raises(dataclasses.FrozenInstanceError):
        song.title = "Renamed"  # type: ignore[misc]


@pytest.mark.parametrize("field", ["id", "title"])
def test_empty_identifiers_are_rejected(field: str) -> None:
    """Blank ids and titles break the invariants of a playable track."""
    with pytest.raises(ValidationError):
        make_song(**{field: "   "})


def test_negative_duration_is_rejected() -> None:
    """A duration is never negative; unknown durations use 0.0 instead."""
    with pytest.raises(ValidationError):
        make_song(duration=-1.0)

    assert make_song(duration=0.0).duration == 0.0


def test_both_audio_sources_are_available() -> None:
    """Local and Spotify are two separate, equally valid sources."""
    local = make_song(id="local-1", source=AudioSourceType.LOCAL)
    spotify = make_song(id="spotify-1", source=AudioSourceType.SPOTIFY)

    assert local.source is AudioSourceType.LOCAL
    assert spotify.source is AudioSourceType.SPOTIFY
    assert AudioSourceType.LOCAL is not AudioSourceType.SPOTIFY


def test_spotify_songs_can_carry_an_external_url() -> None:
    """Spotify tracks link back to the catalogue page."""
    song = make_song(
        source=AudioSourceType.SPOTIFY, external_url="https://open.spotify.com/track/x"
    )

    assert song.external_url is not None


def test_unavailable_local_song_after_reload() -> None:
    """LOCAL-006: metadata survives, the file must be re-selected."""
    song = make_song(available=False)

    assert song.available is False


def test_duration_label_formats_minutes_and_seconds() -> None:
    """The UI shows ``m:ss``; unknown durations render as ``0:00``."""
    assert make_song(duration=183.0).duration_label == "3:03"
    assert make_song(duration=600.0).duration_label == "10:00"
    assert make_song(duration=0.0).duration_label == "0:00"
    assert make_song(duration=59.9).duration_label == "0:59"


def test_equal_songs_are_interchangeable() -> None:
    """Value semantics: search-by-value in the list relies on this."""
    assert make_song() == make_song()
    assert make_song() != make_song(title="Other")
