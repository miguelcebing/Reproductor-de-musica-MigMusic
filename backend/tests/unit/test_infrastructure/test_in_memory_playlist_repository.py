"""Tests for ``InMemoryPlaylistRepository``."""

from __future__ import annotations

from migmusic.domain import AudioSourceType, Playlist, Song
from migmusic.infrastructure.persistence import InMemoryPlaylistRepository


def test_save_then_find_returns_the_same_playlist() -> None:
    """The aggregate round-trips without copying (one source of truth)."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Road trip")

    repository.save(playlist)

    assert repository.find_by_id(playlist.id) is playlist


def test_find_by_id_returns_none_for_unknown_id() -> None:
    """Unknown ids are a miss, not an error."""
    repository = InMemoryPlaylistRepository()

    assert repository.find_by_id("does-not-exist") is None


def test_save_upserts_instead_of_duplicating() -> None:
    """Saving the same id twice keeps a single entry."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Road trip")

    repository.save(playlist)
    playlist.rename("Road trip 2")
    repository.save(playlist)

    assert len(repository.list_all()) == 1
    assert repository.list_all()[0].name == "Road trip 2"


def test_list_all_preserves_insertion_order() -> None:
    """Playlists keep the order in which they were created."""
    repository = InMemoryPlaylistRepository()
    first, second = Playlist("First"), Playlist("Second")

    repository.save(second)
    repository.save(first)
    repository.save(second)

    assert [playlist.name for playlist in repository.list_all()] == ["Second", "First"]


def test_delete_reports_whether_it_removed_something() -> None:
    """Deletion tells the caller whether an entry existed (404 or 204)."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Road trip")
    repository.save(playlist)

    assert repository.delete(playlist.id) is True
    assert repository.delete(playlist.id) is False
    assert repository.list_all() == []


def test_songs_are_stored_with_the_playlist() -> None:
    """The whole aggregate, not just its id, survives the round trip."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Road trip")
    playlist.add(
        Song(
            id="local-1",
            title="Night",
            artist="MigMusic",
            source=AudioSourceType.LOCAL,
            duration=180.0,
        )
    )

    repository.save(playlist)

    stored = repository.find_by_id(playlist.id)
    assert stored is not None
    assert [song.title for song in stored] == ["Night"]
    assert stored.size == 1


def test_repository_instances_do_not_share_state() -> None:
    """Two adapters are independent, which is what makes them swappable."""
    first = InMemoryPlaylistRepository()
    second = InMemoryPlaylistRepository()
    first.save(Playlist("Only here"))

    assert second.list_all() == []
    assert len(first.list_all()) == 1
