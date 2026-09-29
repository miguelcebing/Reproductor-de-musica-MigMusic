"""Tests for ``Playlist``, the entity that owns a ``DoublyLinkedList``."""

from __future__ import annotations

import itertools

import pytest

from migmusic.core import ValidationError
from migmusic.domain import (
    AudioSourceType,
    DoublyLinkedList,
    EmptyPlaylistError,
    InvalidPositionError,
    Playlist,
    Song,
)

_COUNTER = itertools.count(1)


def make_song(**overrides: object) -> Song:
    """Build a valid local song with a unique id (usable inside fixtures)."""
    index = next(_COUNTER)
    values: dict[str, object] = {
        "id": f"local-{index}",
        "title": "Untitled",
        "artist": "MigMusic",
        "source": AudioSourceType.LOCAL,
        "duration": 120.0,
    }
    values.update(overrides)
    return Song(**values)  # type: ignore[arg-type]


@pytest.fixture
def playlist() -> Playlist:
    """A playlist pre-filled with three songs, cursor on the first one."""
    return Playlist("Road trip", songs=[make_song(title=title) for title in ("A", "B", "C")])


def titles(playlist: Playlist) -> list[str]:
    """Titles in order."""
    return [song.title for song in playlist]


def test_playlist_owns_a_real_linked_list(playlist: Playlist) -> None:
    """Composition: the playlist delegates structure to the list, never arrays."""
    assert isinstance(playlist.songs, DoublyLinkedList)
    assert playlist.songs.head is not None
    assert playlist.songs.tail is not None
    assert playlist.songs is playlist.songs  # stable reference, never replaced


def test_playlist_has_a_generated_id() -> None:
    """Ids are UUIDs so playlists can be persisted (``PLAYLIST-001 = B``)."""
    first, second = Playlist("One"), Playlist("Two")

    assert first.id != second.id
    assert len(first.id) == 36


def test_playlist_accepts_an_explicit_id() -> None:
    """Repositories supply the id when loading from the database."""
    playlist = Playlist("Imported", playlist_id="11111111-1111-1111-1111-111111111111")

    assert playlist.id == "11111111-1111-1111-1111-111111111111"


def test_empty_playlist() -> None:
    """Size, length and cursor agree on an empty playlist."""
    fresh = Playlist("Empty")

    assert len(fresh) == 0
    assert fresh.size == 0
    assert fresh.current is None
    assert fresh.to_list() == []
    assert fresh.move_next() is False
    assert fresh.move_previous() is False

    fresh.add(make_song(title="First"))
    assert len(fresh) == 1
    assert fresh.current is not None and fresh.current.title == "First"


def test_name_is_trimmed_and_validated() -> None:
    """Names are cleaned on creation and on rename (``PLAYLIST-003``)."""
    playlist = Playlist("   Chill   ")

    assert playlist.name == "Chill"

    with pytest.raises(ValidationError):
        playlist.rename("   ")

    with pytest.raises(ValidationError):
        playlist.rename("x" * 121)

    with pytest.raises(ValidationError):
        Playlist("")


def test_rename_keeps_identity() -> None:
    """Renaming never changes the id used by the API."""
    playlist = Playlist("Old")
    original = playlist.id

    playlist.rename("New")

    assert playlist.name == "New"
    assert playlist.id == original


def test_add_appends_and_moves_nothing(playlist: Playlist) -> None:
    """``add`` is O(1) and leaves the cursor where it was."""
    before = playlist.current

    playlist.add(make_song(title="D"))

    assert titles(playlist) == ["A", "B", "C", "D"]
    assert playlist.current is before
    playlist.songs.assert_invariants()


def test_insert_at_supports_drag_and_drop(playlist: Playlist) -> None:
    """Reordering is expressed as ``insert_at`` (``FEAT-001-e``)."""
    moved = playlist.remove_at(0)
    playlist.insert_at(2, moved)

    assert titles(playlist) == ["B", "C", "A"]
    playlist.songs.assert_invariants()


def test_insert_at_reports_invalid_positions(playlist: Playlist) -> None:
    """Positions outside ``0 .. size`` are domain errors."""
    with pytest.raises(InvalidPositionError):
        playlist.insert_at(99, make_song())
    with pytest.raises(InvalidPositionError):
        playlist.insert_at(-1, make_song())


def test_remove_at_reports_invalid_positions(playlist: Playlist) -> None:
    """Only existing songs can be removed."""
    with pytest.raises(InvalidPositionError):
        playlist.remove_at(3)
    with pytest.raises(EmptyPlaylistError):
        Playlist("Empty").remove_at(0)


def test_find_and_membership(playlist: Playlist) -> None:
    """Search inside the playlist uses ``find`` (``PLAYLIST-008``)."""
    songs = playlist.to_list()

    assert playlist.find(songs[1]) == 1
    assert playlist.find(make_song(title="Z")) is None
    assert songs[0] in playlist
    assert make_song(title="Z") not in playlist
    assert playlist.find_by(lambda song: song.title.startswith("C")) == 2
    assert playlist.find_by(lambda song: song.title.startswith("Z")) is None


def test_cursor_navigation_stops_at_the_edges(playlist: Playlist) -> None:
    """``PLAYLIST-009 = A`` is respected through the playlist facade."""
    assert playlist.current is not None and playlist.current.title == "A"

    assert playlist.move_previous() is False
    assert playlist.move_previous() is False

    assert playlist.move_next() is True
    assert playlist.move_next() is True
    assert playlist.current is not None and playlist.current.title == "C"

    assert playlist.move_next() is False
    assert playlist.current is not None and playlist.current.title == "C"


def test_move_to_selects_a_song(playlist: Playlist) -> None:
    """Clicking a row selects it."""
    selected = playlist.move_to(2)

    assert selected.title == "C"
    assert playlist.current is selected

    with pytest.raises(InvalidPositionError):
        playlist.move_to(5)


def test_duplicates_are_allowed() -> None:
    """No decision forbids queueing the same song twice."""
    playlist = Playlist("Dupes")
    song = make_song(title="Same")

    playlist.add(song)
    playlist.add(song)

    assert titles(playlist) == ["Same", "Same"]
    assert playlist.find(song) == 0


def test_serialisation_and_display_helpers(playlist: Playlist) -> None:
    """DTO-oriented views: snapshot, iteration and a readable repr."""
    snapshot = playlist.to_list()

    assert [song.title for song in snapshot] == ["A", "B", "C"]
    assert [song.title for song in playlist] == ["A", "B", "C"]
    assert repr(playlist) == "Playlist('Road trip', size=3)"


def test_playlist_starting_empty_then_filled() -> None:
    """A playlist built through the UI keeps its invariants at every step."""
    playlist = Playlist("Fresh")
    playlist.songs.assert_invariants()

    playlist.add(make_song(title="One"))
    playlist.songs.assert_invariants()
    playlist.add(make_song(title="Two"))
    playlist.songs.assert_invariants()

    removed = playlist.remove_at(1)
    playlist.songs.assert_invariants()

    assert removed.title == "Two"
    assert titles(playlist) == ["One"]
