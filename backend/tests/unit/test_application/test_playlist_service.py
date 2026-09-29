"""Tests for ``PlaylistService``."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from migmusic.application.services import PlaylistService
from migmusic.core import ValidationError
from migmusic.domain import (
    EmptyPlaylistError,
    InvalidPositionError,
    Playlist,
    PlaylistNotFoundError,
    Song,
)
from migmusic.infrastructure.persistence import InMemoryPlaylistRepository


def test_create_persists_an_empty_playlist(
    playlist_service: PlaylistService, repository: InMemoryPlaylistRepository
) -> None:
    """``PLAYLIST-002``: a created playlist is immediately readable."""
    playlist = playlist_service.create("Road trip")

    assert playlist.name == "Road trip"
    assert playlist.size == 0
    assert repository.find_by_id(playlist.id) is playlist


def test_create_rejects_an_empty_name(playlist_service: PlaylistService) -> None:
    """Names are validated by the domain, not by the router."""
    with pytest.raises(ValidationError):
        playlist_service.create("   ")


def test_list_returns_every_stored_playlist(playlist_service: PlaylistService) -> None:
    """``PLAYLIST-001 = B``: several playlists coexist."""
    playlist_service.create("First")
    playlist_service.create("Second")

    assert [playlist.name for playlist in playlist_service.list()] == ["First", "Second"]


def test_get_returns_the_playlist(playlist_service: PlaylistService) -> None:
    """Reads by id are the backbone of every other use case."""
    created = playlist_service.create("Road trip")

    assert playlist_service.get(created.id) is created


def test_get_unknown_playlist_raises_not_found(playlist_service: PlaylistService) -> None:
    """404 for an unknown id, raised once and translated in one place."""
    with pytest.raises(PlaylistNotFoundError):
        playlist_service.get("missing")


def test_rename_updates_the_stored_name(
    playlist_service: PlaylistService, repository: InMemoryPlaylistRepository
) -> None:
    """``PLAYLIST-003``: rename persists through the repository."""
    playlist = playlist_service.create("Old")

    playlist_service.rename(playlist.id, "New")

    stored = repository.find_by_id(playlist.id)
    assert stored is not None
    assert stored.name == "New"


def test_rename_unknown_playlist_raises_not_found(playlist_service: PlaylistService) -> None:
    """Renaming nothing is a 404, not a silent success."""
    with pytest.raises(PlaylistNotFoundError):
        playlist_service.rename("missing", "Whatever")


def test_rename_rejects_an_empty_name(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """The same domain rule applies on rename as on create."""
    playlist = seed_playlist()

    with pytest.raises(ValidationError):
        playlist_service.rename(playlist.id, "  ")


def test_delete_removes_it_from_the_repository(
    playlist_service: PlaylistService, repository: InMemoryPlaylistRepository
) -> None:
    """Delete answers with a real removal."""
    playlist = playlist_service.create("Gone")

    playlist_service.delete(playlist.id)

    assert repository.find_by_id(playlist.id) is None


def test_delete_unknown_playlist_raises_not_found(playlist_service: PlaylistService) -> None:
    """Deleting an unknown id is a 404."""
    with pytest.raises(PlaylistNotFoundError):
        playlist_service.delete("missing")


def test_add_song_appends_to_the_end(
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
    make_song: Callable[..., Song],
) -> None:
    """Default position is the tail (``UX-003``)."""
    playlist = seed_playlist(count=2)
    extra = make_song()

    playlist_service.add_song(playlist.id, extra)

    assert playlist.to_list()[-1] == extra
    assert playlist.size == 3


def test_add_song_at_a_position_inserts_mid_list(
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
    make_song: Callable[..., Song],
) -> None:
    """``insert_at`` puts the song exactly where the modal asked."""
    playlist = seed_playlist(count=3)
    extra = make_song()

    playlist_service.add_song(playlist.id, extra, index=1)

    assert [song.id for song in playlist][1] == extra.id


def test_add_song_at_an_invalid_position_raises(
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
    make_song: Callable[..., Song],
) -> None:
    """Out-of-range inserts are 422, raised by the list itself."""
    playlist = seed_playlist(count=2)

    with pytest.raises(InvalidPositionError):
        playlist_service.add_song(playlist.id, make_song(), index=99)


def test_remove_song_returns_it_and_shrinks_the_list(
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
) -> None:
    """The caller gets the removed song back (useful for undo)."""
    playlist = seed_playlist(count=3)
    removed_id = playlist.to_list()[1].id

    removed = playlist_service.remove_song(playlist.id, 1)

    assert removed.id == removed_id
    assert playlist.size == 2


def test_remove_from_an_empty_playlist_raises(
    playlist_service: PlaylistService,
) -> None:
    """Removing from nothing is a 400 ``EmptyPlaylistError``."""
    empty = playlist_service.create("Empty")

    with pytest.raises(EmptyPlaylistError):
        playlist_service.remove_song(empty.id, 0)


def test_remove_out_of_range_raises(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Index bounds belong to the list, not to the router."""
    playlist = seed_playlist(count=2)

    with pytest.raises(InvalidPositionError):
        playlist_service.remove_song(playlist.id, 5)


def test_move_song_reorders(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``FEAT-001-e``: drag and drop is remove + insert."""
    playlist = seed_playlist(count=3)
    before = [song.id for song in playlist]

    playlist_service.move_song(playlist.id, 0, 2)

    assert [song.id for song in playlist] == [before[1], before[2], before[0]]


def test_move_song_to_the_same_index_is_a_no_op(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Dropping a song where it already is must not touch the list."""

    class RecordingRepository(InMemoryPlaylistRepository):
        def __init__(self) -> None:
            super().__init__()
            self.saves: list[Playlist] = []

        def save(self, playlist: Playlist) -> None:
            self.saves.append(playlist)
            super().save(playlist)

    recording = RecordingRepository()
    service = PlaylistService(recording)
    playlist = seed_playlist(count=3)
    recording.save(playlist)
    recording.saves.clear()
    before = [song.id for song in playlist]

    service.move_song(playlist.id, 1, 1)

    assert [song.id for song in playlist] == before
    assert recording.saves == []


def test_service_never_builds_an_adapter() -> None:
    """DIP: the service only knows the port, so it can be swapped at will."""

    class RecordingRepository(InMemoryPlaylistRepository):
        def __init__(self) -> None:
            super().__init__()
            self.saved = False

        def save(self, playlist: Playlist) -> None:
            self.saved = True
            super().save(playlist)

    recording = RecordingRepository()

    PlaylistService(recording).create("Anything")

    assert recording.saved is True


def test_move_song_with_an_invalid_source_raises(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Both bounds are validated *before* mutating."""
    playlist = seed_playlist(count=3)
    before = [song.id for song in playlist]

    with pytest.raises(InvalidPositionError):
        playlist_service.move_song(playlist.id, 7, 0)

    assert [song.id for song in playlist] == before


def test_move_song_with_an_invalid_target_raises(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """A target beyond the resulting size cannot insert."""
    playlist = seed_playlist(count=3)
    before = [song.id for song in playlist]

    with pytest.raises(InvalidPositionError):
        playlist_service.move_song(playlist.id, 0, 5)

    assert [song.id for song in playlist] == before
