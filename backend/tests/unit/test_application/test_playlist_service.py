"""Tests for ``PlaylistService``."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from migmusic.application.services import PlaylistService
from migmusic.core import ValidationError
from migmusic.domain import (
    EmptyPlaylistError,
    InvalidPositionError,
    ItemNotFoundError,
    Playlist,
    PlaylistNotFoundError,
    Song,
)
from migmusic.infrastructure.persistence import InMemoryPlaylistRepository

OWNER = "device-a"
OTHER = "device-b"


def test_create_persists_an_empty_playlist(
    playlist_service: PlaylistService, repository: InMemoryPlaylistRepository
) -> None:
    """``PLAYLIST-002``: a created playlist is immediately readable."""
    playlist = playlist_service.create("Road trip", owner_id=OWNER)

    assert playlist.name == "Road trip"
    assert playlist.size == 0
    assert repository.find_by_id(playlist.id, owner_id=OWNER) is playlist


def test_create_rejects_an_empty_name(playlist_service: PlaylistService) -> None:
    """Names are validated by the domain, not by the router."""
    with pytest.raises(ValidationError):
        playlist_service.create("   ", owner_id=OWNER)


def test_list_returns_the_callers_playlists(playlist_service: PlaylistService) -> None:
    """``PLAYLIST-001 = B``: several playlists coexist for one owner."""
    playlist_service.create("First", owner_id=OWNER)
    playlist_service.create("Second", owner_id=OWNER)

    assert [playlist.name for playlist in playlist_service.list(owner_id=OWNER)] == [
        "First",
        "Second",
    ]


def test_create_stamps_the_owner_device(playlist_service: PlaylistService) -> None:
    """A playlist belongs to the device that asked for it (UX isolation)."""
    playlist = playlist_service.create("Phone mix", owner_id=OWNER)

    assert [item.id for item in playlist_service.list(owner_id=OWNER)] == [playlist.id]
    assert playlist_service.list(owner_id=OTHER) == []


def test_edits_keep_the_owner_device(playlist_service: PlaylistService) -> None:
    """Renaming must never re-home a playlist to another device."""
    playlist = playlist_service.create("Owned", owner_id=OWNER)

    playlist_service.rename(playlist.id, "Renamed", owner_id=OWNER)

    assert [item.name for item in playlist_service.list(owner_id=OWNER)] == ["Renamed"]
    assert playlist_service.list(owner_id=OTHER) == []


def test_get_returns_the_playlist(playlist_service: PlaylistService) -> None:
    """Reads by id are the backbone of every other use case."""
    created = playlist_service.create("Road trip", owner_id=OWNER)

    assert playlist_service.get(created.id, owner_id=OWNER) is created


def test_get_unknown_playlist_raises_not_found(playlist_service: PlaylistService) -> None:
    """404 for an unknown id, raised once and translated in one place."""
    with pytest.raises(PlaylistNotFoundError):
        playlist_service.get("missing", owner_id=OWNER)


def test_get_hides_a_foreign_playlist(playlist_service: PlaylistService) -> None:
    """A playlist owned by another device reads as 404, closing the IDOR hole."""
    playlist = playlist_service.create("Phone mix", owner_id=OWNER)

    with pytest.raises(PlaylistNotFoundError):
        playlist_service.get(playlist.id, owner_id=OTHER)


def test_rename_updates_the_stored_name(
    playlist_service: PlaylistService, repository: InMemoryPlaylistRepository
) -> None:
    """``PLAYLIST-003``: rename persists through the repository."""
    playlist = playlist_service.create("Old", owner_id=OWNER)

    playlist_service.rename(playlist.id, "New", owner_id=OWNER)

    stored = repository.find_by_id(playlist.id, owner_id=OWNER)
    assert stored is not None
    assert stored.name == "New"


def test_rename_unknown_playlist_raises_not_found(playlist_service: PlaylistService) -> None:
    """Renaming nothing is a 404, not a silent success."""
    with pytest.raises(PlaylistNotFoundError):
        playlist_service.rename("missing", "Whatever", owner_id=OWNER)


def test_rename_refuses_a_foreign_playlist(playlist_service: PlaylistService) -> None:
    """Another device cannot rename a playlist it does not own."""
    playlist = playlist_service.create("Phone mix", owner_id=OWNER)

    with pytest.raises(PlaylistNotFoundError):
        playlist_service.rename(playlist.id, "Hijacked", owner_id=OTHER)

    assert playlist_service.get(playlist.id, owner_id=OWNER).name == "Phone mix"


def test_rename_rejects_an_empty_name(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """The same domain rule applies on rename as on create."""
    playlist = seed_playlist()

    with pytest.raises(ValidationError):
        playlist_service.rename(playlist.id, "  ", owner_id=OWNER)


def test_delete_removes_it_from_the_repository(
    playlist_service: PlaylistService, repository: InMemoryPlaylistRepository
) -> None:
    """Delete answers with a real removal."""
    playlist = playlist_service.create("Gone", owner_id=OWNER)

    playlist_service.delete(playlist.id, owner_id=OWNER)

    assert repository.find_by_id(playlist.id, owner_id=OWNER) is None


def test_delete_unknown_playlist_raises_not_found(playlist_service: PlaylistService) -> None:
    """Deleting an unknown id is a 404."""
    with pytest.raises(PlaylistNotFoundError):
        playlist_service.delete("missing", owner_id=OWNER)


def test_delete_refuses_a_foreign_playlist(playlist_service: PlaylistService) -> None:
    """Another device cannot delete a playlist it does not own."""
    playlist = playlist_service.create("Phone mix", owner_id=OWNER)

    with pytest.raises(PlaylistNotFoundError):
        playlist_service.delete(playlist.id, owner_id=OTHER)

    assert playlist_service.get(playlist.id, owner_id=OWNER).name == "Phone mix"


def test_add_song_appends_to_the_end(
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
    make_song: Callable[..., Song],
) -> None:
    """Default position is the tail (``UX-003``)."""
    playlist = seed_playlist(count=2)
    extra = make_song()

    playlist_service.add_song(playlist.id, extra, owner_id=OWNER)

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

    playlist_service.add_song(playlist.id, extra, index=1, owner_id=OWNER)

    assert [song.id for song in playlist][1] == extra.id


def test_add_song_at_an_invalid_position_raises(
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
    make_song: Callable[..., Song],
) -> None:
    """Out-of-range inserts are 422, raised by the list itself."""
    playlist = seed_playlist(count=2)

    with pytest.raises(InvalidPositionError):
        playlist_service.add_song(playlist.id, make_song(), index=99, owner_id=OWNER)


def test_add_song_refuses_a_foreign_playlist(
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
    make_song: Callable[..., Song],
) -> None:
    """Another device cannot add songs to a playlist it does not own."""
    playlist = seed_playlist(count=2)

    with pytest.raises(PlaylistNotFoundError):
        playlist_service.add_song(playlist.id, make_song(), owner_id=OTHER)

    assert playlist.size == 2


def test_remove_song_returns_it_and_shrinks_the_list(
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
) -> None:
    """The caller gets the removed song back (useful for undo)."""
    playlist = seed_playlist(count=3)
    removed_id = playlist.to_list()[1].id

    removed = playlist_service.remove_song(playlist.id, 1, owner_id=OWNER)

    assert removed.id == removed_id
    assert playlist.size == 2


def test_remove_from_an_empty_playlist_raises(
    playlist_service: PlaylistService,
) -> None:
    """Removing from nothing is a 400 ``EmptyPlaylistError``."""
    empty = playlist_service.create("Empty", owner_id=OWNER)

    with pytest.raises(EmptyPlaylistError):
        playlist_service.remove_song(empty.id, 0, owner_id=OWNER)


def test_remove_out_of_range_raises(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Index bounds belong to the list, not to the router."""
    playlist = seed_playlist(count=2)

    with pytest.raises(InvalidPositionError):
        playlist_service.remove_song(playlist.id, 5, owner_id=OWNER)


def test_move_song_reorders(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``FEAT-001-e``: drag and drop is remove + insert."""
    playlist = seed_playlist(count=3)
    before = [song.id for song in playlist]

    playlist_service.move_song(playlist.id, 0, 2, owner_id=OWNER)

    assert [song.id for song in playlist] == [before[1], before[2], before[0]]


def test_move_song_to_the_same_index_is_a_no_op(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Dropping a song where it already is must not touch the list."""

    class RecordingRepository(InMemoryPlaylistRepository):
        def __init__(self) -> None:
            super().__init__()
            self.saves: list[Playlist] = []

        def save(self, playlist: Playlist, *, owner_id: str) -> None:
            self.saves.append(playlist)
            super().save(playlist, owner_id=owner_id)

    recording = RecordingRepository()
    service = PlaylistService(recording)
    playlist = seed_playlist(count=3)
    recording.save(playlist, owner_id=OWNER)
    recording.saves.clear()
    before = [song.id for song in playlist]

    service.move_song(playlist.id, 1, 1, owner_id=OWNER)

    assert [song.id for song in playlist] == before
    assert recording.saves == []


def test_service_never_builds_an_adapter() -> None:
    """DIP: the service only knows the port, so it can be swapped at will."""

    class RecordingRepository(InMemoryPlaylistRepository):
        def __init__(self) -> None:
            super().__init__()
            self.saved = False

        def save(self, playlist: Playlist, *, owner_id: str) -> None:
            self.saved = True
            super().save(playlist, owner_id=owner_id)

    recording = RecordingRepository()

    PlaylistService(recording).create("Anything", owner_id=OWNER)

    assert recording.saved is True


def test_move_song_with_an_invalid_source_raises(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Both bounds are validated *before* mutating."""
    playlist = seed_playlist(count=3)
    before = [song.id for song in playlist]

    with pytest.raises(InvalidPositionError):
        playlist_service.move_song(playlist.id, 7, 0, owner_id=OWNER)

    assert [song.id for song in playlist] == before


def test_move_song_with_an_invalid_target_raises(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """A target beyond the resulting size cannot insert."""
    playlist = seed_playlist(count=3)
    before = [song.id for song in playlist]

    with pytest.raises(InvalidPositionError):
        playlist_service.move_song(playlist.id, 0, 5, owner_id=OWNER)

    assert [song.id for song in playlist] == before


def test_set_favorite_persists_the_flag(
    playlist_service: PlaylistService,
    repository: InMemoryPlaylistRepository,
    seed_playlist: Callable[..., Playlist],
) -> None:
    """``FEAT-001-b``: the heart is stored, not just answered."""
    playlist = seed_playlist(count=2)

    song = playlist_service.set_favorite(playlist.id, 1, True, owner_id=OWNER)

    assert song.favorite is True
    stored = repository.find_by_id(playlist.id, owner_id=OWNER)
    assert stored is not None
    assert stored.song_at(1).favorite is True
    assert stored.song_at(0).favorite is False


def test_set_favorite_on_an_unknown_playlist_raises(
    playlist_service: PlaylistService,
) -> None:
    """Same 404 envelope as every other missing playlist."""
    with pytest.raises(PlaylistNotFoundError):
        playlist_service.set_favorite("missing", 0, True, owner_id=OWNER)


def test_set_favorite_out_of_range_raises(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Bounds still belong to the list, not to the service."""
    playlist = seed_playlist(count=3)

    with pytest.raises(InvalidPositionError):
        playlist_service.set_favorite(playlist.id, 9, True, owner_id=OWNER)


def test_find_song_returns_the_first_match(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``FEAT-001-c``: ``find_by`` walks the list and stops at the first hit."""
    playlist = seed_playlist(count=3)

    index, song = playlist_service.find_song(playlist.id, "song 2", owner_id=OWNER)

    assert index == 1
    assert song.title == "Song 2"


def test_find_song_is_case_insensitive_over_title_and_artist(
    playlist_service: PlaylistService, make_song: Callable[..., Song]
) -> None:
    """Matching runs on both fields, folded so 'MIGMUSIC' finds the artist."""
    playlist = playlist_service.create("Road trip", owner_id=OWNER)
    playlist_service.add_song(
        playlist.id, make_song(title="Nocturne", artist="Chopin"), owner_id=OWNER
    )

    index, song = playlist_service.find_song(playlist.id, "NOCTURNE", owner_id=OWNER)
    assert index == 0 and song.title == "Nocturne"

    index, song = playlist_service.find_song(playlist.id, "chop", owner_id=OWNER)
    assert index == 0 and song.artist == "Chopin"


def test_find_song_without_matches_raises_not_found(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """A miss is a 404, so the UI can answer 'no matches' quietly."""
    playlist = seed_playlist(count=3)

    with pytest.raises(ItemNotFoundError):
        playlist_service.find_song(playlist.id, "zzz", owner_id=OWNER)


def test_find_song_rejects_blank_text(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Empty queries never walk the list."""
    playlist = seed_playlist(count=3)

    with pytest.raises(ValidationError):
        playlist_service.find_song(playlist.id, "   ", owner_id=OWNER)


def test_find_song_never_moves_the_cursor(
    playlist_service: PlaylistService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Searching must not change which song is playing."""
    playlist = seed_playlist(count=3)
    playlist.move_to(2)

    index, _song = playlist_service.find_song(playlist.id, "song 1", owner_id=OWNER)

    assert index == 0
    assert playlist.current_index == 2
