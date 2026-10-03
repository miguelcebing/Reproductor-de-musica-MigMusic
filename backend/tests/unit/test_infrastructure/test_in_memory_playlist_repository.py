"""Tests for ``InMemoryPlaylistRepository``."""

from __future__ import annotations

from migmusic.domain import AudioSourceType, Playlist, Song
from migmusic.infrastructure.persistence import InMemoryPlaylistRepository

OWNER = "device-a"


def test_save_then_find_returns_the_same_playlist() -> None:
    """The aggregate round-trips without copying (one source of truth)."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Road trip")

    repository.save(playlist, owner_id=OWNER)

    assert repository.find_by_id(playlist.id, owner_id=OWNER) is playlist


def test_find_by_id_returns_none_for_unknown_id() -> None:
    """Unknown ids are a miss, not an error."""
    repository = InMemoryPlaylistRepository()

    assert repository.find_by_id("does-not-exist", owner_id=OWNER) is None


def test_save_upserts_instead_of_duplicating() -> None:
    """Saving the same id twice keeps a single entry."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Road trip")

    repository.save(playlist, owner_id=OWNER)
    playlist.rename("Road trip 2")
    repository.save(playlist, owner_id=OWNER)

    assert len(repository.list_all(owner_id=OWNER)) == 1
    assert repository.list_all(owner_id=OWNER)[0].name == "Road trip 2"


def test_list_all_preserves_insertion_order() -> None:
    """Playlists keep the order in which they were created."""
    repository = InMemoryPlaylistRepository()
    first, second = Playlist("First"), Playlist("Second")

    repository.save(second, owner_id=OWNER)
    repository.save(first, owner_id=OWNER)
    repository.save(second, owner_id=OWNER)

    assert [playlist.name for playlist in repository.list_all(owner_id=OWNER)] == [
        "Second",
        "First",
    ]


def test_delete_reports_whether_it_removed_something() -> None:
    """Deletion tells the caller whether an entry existed (404 or 204)."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Road trip")
    repository.save(playlist, owner_id=OWNER)

    assert repository.delete(playlist.id, owner_id=OWNER) is True
    assert repository.delete(playlist.id, owner_id=OWNER) is False
    assert repository.list_all(owner_id=OWNER) == []


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

    repository.save(playlist, owner_id=OWNER)

    stored = repository.find_by_id(playlist.id, owner_id=OWNER)
    assert stored is not None
    assert [song.title for song in stored] == ["Night"]
    assert stored.size == 1


def test_repository_instances_do_not_share_state() -> None:
    """Two adapters are independent, which is what makes them swappable."""
    first = InMemoryPlaylistRepository()
    second = InMemoryPlaylistRepository()
    first.save(Playlist("Only here"), owner_id=OWNER)

    assert second.list_all(owner_id=OWNER) == []
    assert len(first.list_all(owner_id=OWNER)) == 1


def test_list_all_scopes_to_one_device() -> None:
    """Each device sees only its own lists."""
    repository = InMemoryPlaylistRepository()
    repository.save(Playlist("Phone mix"), owner_id="device-a")
    repository.save(Playlist("Laptop mix"), owner_id="device-b")

    assert [p.name for p in repository.list_all(owner_id="device-a")] == ["Phone mix"]
    assert [p.name for p in repository.list_all(owner_id="device-b")] == ["Laptop mix"]


def test_find_by_id_hides_foreign_playlists() -> None:
    """A playlist owned by another device reads as missing (404, not 403)."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Phone mix")
    repository.save(playlist, owner_id="device-a")

    assert repository.find_by_id(playlist.id, owner_id="device-b") is None


def test_delete_refuses_a_foreign_playlist() -> None:
    """Another device's playlist cannot be deleted, and stays listed."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Phone mix")
    repository.save(playlist, owner_id="device-a")

    assert repository.delete(playlist.id, owner_id="device-b") is False
    assert [p.name for p in repository.list_all(owner_id="device-a")] == ["Phone mix"]


def test_later_saves_keep_the_first_owner() -> None:
    """An edit rewrites the aggregate, never its device."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Owned")
    repository.save(playlist, owner_id="device-a")

    playlist.rename("Renamed")
    repository.save(playlist, owner_id="device-a")

    assert [p.name for p in repository.list_all(owner_id="device-a")] == ["Renamed"]
    assert repository.list_all(owner_id="device-b") == []


def test_delete_forgets_the_owner_too() -> None:
    """Removing a playlist releases its device stamp as well."""
    repository = InMemoryPlaylistRepository()
    playlist = Playlist("Gone")
    repository.save(playlist, owner_id="device-a")

    assert repository.delete(playlist.id, owner_id="device-a") is True
    assert repository.list_all(owner_id="device-a") == []


def test_delete_all_wipes_every_owner() -> None:
    """The development reset removes playlists of every device at once."""
    repository = InMemoryPlaylistRepository()
    repository.save(Playlist("A"), owner_id="device-a")
    repository.save(Playlist("B"), owner_id="device-b")

    assert repository.delete_all() == 2
    assert repository.list_all(owner_id="device-a") == []
    assert repository.list_all(owner_id="device-b") == []
