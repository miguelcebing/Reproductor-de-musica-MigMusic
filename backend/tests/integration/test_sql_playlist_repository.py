"""Contract tests for the PostgreSQL adapter (`DB-002`, `DB-003`, `ADR-004`).

The suite runs against a real PostgreSQL: ``TEST_DATABASE_URL`` when provided
(CI or a developer pointing at Neon), otherwise the embedded ``pgserver``
dev dependency boots a throwaway server — no Docker (`DEPLOY-004`) required.
"""

from __future__ import annotations

import atexit
import os
import tempfile
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

import psycopg
import pytest
from psycopg.rows import dict_row

from migmusic.domain.entities.playlist import Playlist
from migmusic.infrastructure.persistence import SqlPlaylistRepository

if TYPE_CHECKING:
    from migmusic.domain.entities.song import Song

try:  # Embedded PostgreSQL; absent only in environments that override the DSN.
    import pgserver
except ImportError:  # pragma: no cover - depends on the environment
    pgserver = None  # type: ignore[assignment]


def _resolve_dsn() -> str:
    """Prefer ``TEST_DATABASE_URL``; else boot an embedded server once."""
    provided = os.environ.get("TEST_DATABASE_URL", "")
    if provided:
        return provided
    if pgserver is None:  # pragma: no cover - depends on the environment
        return ""
    try:
        data_dir = Path(tempfile.gettempdir()) / "migmusic-test-pg"
        server = pgserver.get_server(str(data_dir))
        atexit.register(server.cleanup)
        return server.get_uri()
    except Exception:  # pragma: no cover - skip instead of failing collection
        return ""


_DSN = _resolve_dsn()

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _DSN, reason="no PostgreSQL available (set TEST_DATABASE_URL)"),
]


@pytest.fixture
def sql_repository() -> Iterator[SqlPlaylistRepository]:
    """Fresh schema state per test, then an adapter over it."""
    repository = SqlPlaylistRepository(_DSN)
    with psycopg.connect(_DSN) as connection:
        connection.execute("TRUNCATE playlists, songs")
    yield repository


def _raw_songs(playlist_id: str) -> list[dict[str, Any]]:
    """Read the stored rows verbatim, to assert the `DB-003` mapping."""
    with psycopg.connect(_DSN, row_factory=dict_row) as connection:
        return connection.execute(
            "SELECT position, song_id, prev_id, next_id, favorite "
            "FROM songs WHERE playlist_id = %s ORDER BY position",
            (playlist_id,),
        ).fetchall()


def test_save_and_find_round_trip(
    sql_repository: SqlPlaylistRepository, make_song: Callable[..., Song]
) -> None:
    song = make_song(
        title="Nocturne",
        duration=123.45,
        album="Midnight",
        artwork_url="https://img/cover.jpg",
        external_url="https://open.spotify.com/track/1",
        favorite=True,
        available=False,
    )
    playlist = Playlist("Road trip", songs=[song])
    sql_repository.save(playlist)

    loaded = sql_repository.find_by_id(playlist.id)

    assert loaded is not None
    assert loaded.id == playlist.id
    assert loaded.name == "Road trip"
    assert loaded.size == 1
    assert loaded.song_at(0) == song
    assert loaded.song_at(0).favorite is True
    assert loaded.song_at(0).available is False


def test_find_missing_playlist_returns_none(sql_repository: SqlPlaylistRepository) -> None:
    assert sql_repository.find_by_id("nope") is None


def test_save_upserts_name_and_rewrites_songs(
    sql_repository: SqlPlaylistRepository, make_song: Callable[..., Song]
) -> None:
    playlist = Playlist("First", songs=[make_song()])
    sql_repository.save(playlist)
    playlist.rename("Second")
    playlist.remove_at(0)
    playlist.add(make_song(title="Replacement"))
    sql_repository.save(playlist)

    loaded = sql_repository.find_by_id(playlist.id)

    assert loaded is not None
    assert loaded.name == "Second"
    assert [song.title for song in loaded] == ["Replacement"]


def test_list_all_preserves_insertion_order(
    sql_repository: SqlPlaylistRepository, make_song: Callable[..., Song]
) -> None:
    first = Playlist("A", songs=[make_song()])
    second = Playlist("B")
    third = Playlist("C", songs=[make_song(), make_song()])
    for playlist in (first, second, third):
        sql_repository.save(playlist)

    listed = sql_repository.list_all()

    assert [playlist.id for playlist in listed] == [first.id, second.id, third.id]
    assert [playlist.size for playlist in listed] == [1, 0, 2]


def test_delete_removes_playlist_and_songs(
    sql_repository: SqlPlaylistRepository, make_song: Callable[..., Song]
) -> None:
    playlist = Playlist("Doomed", songs=[make_song(), make_song()])
    sql_repository.save(playlist)

    assert sql_repository.delete(playlist.id) is True
    assert sql_repository.delete(playlist.id) is False
    assert sql_repository.find_by_id(playlist.id) is None
    assert _raw_songs(playlist.id) == []


def test_columns_mirror_the_doubly_linked_list(
    sql_repository: SqlPlaylistRepository, make_song: Callable[..., Song]
) -> None:
    """`DB-003`: prev_id/next_id reflect the links; NULL at both ends."""
    songs = [make_song(), make_song(), make_song()]
    playlist = Playlist("Linked", songs=songs)
    sql_repository.save(playlist)

    rows = _raw_songs(playlist.id)

    assert [row["position"] for row in rows] == [1, 2, 3]
    assert rows[0]["prev_id"] is None
    assert rows[0]["next_id"] == songs[1].id
    assert rows[1]["prev_id"] == songs[0].id
    assert rows[1]["next_id"] == songs[2].id
    assert rows[2]["next_id"] is None
    assert rows[2]["prev_id"] == songs[1].id


def test_duplicates_survive_and_cursor_resets_to_head(
    sql_repository: SqlPlaylistRepository, make_song: Callable[..., Song]
) -> None:
    """Duplicates are legal (`Playlist` docstring) and the cursor resets (ADR-004)."""
    song = make_song()
    playlist = Playlist("Twice", songs=[song, make_song(), song])
    playlist.move_next()
    assert playlist.current_index == 1
    sql_repository.save(playlist)

    loaded = sql_repository.find_by_id(playlist.id)

    assert loaded is not None
    assert loaded.size == 3
    assert loaded.song_at(0).id == song.id
    assert loaded.song_at(2).id == song.id
    assert loaded.current_index == 0


def test_empty_dsn_is_rejected() -> None:
    with pytest.raises(ValueError, match="DSN"):
        SqlPlaylistRepository("   ")
