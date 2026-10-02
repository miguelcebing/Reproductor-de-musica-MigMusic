"""PostgreSQL adapter for the :class:`PlaylistRepository` port (`DB-002`, `DB-003`).

Playlist order lives in ``prev_id`` / ``next_id`` columns mirroring the
doubly linked list, with a dense ``position`` as the deterministic rebuild
path (`ADR-004`): rows are read sorted by ``position`` and the DLL links are
re-created by the ``Playlist`` constructor. Pointers are written on every save
so the stored shape explains itself during the defence.

No ORM: plain parameterised SQL keeps the domain (and this port) free of
infrastructure (`ADR-002`, `ADR-004`).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.domain.entities.playlist import Playlist
from migmusic.domain.entities.song import Song
from migmusic.domain.ports.playlist_repository import PlaylistRepository

# Idempotent schema: safe to run on every process start (`IF NOT EXISTS`).
# ``created_seq`` gives ``list_all`` the insertion order of the in-memory
# adapter; ``position`` is the dense fallback from `ADR-004`. ``owner_id`` is
# the device that created the playlist (UX isolation, null = unscoped).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS playlists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id TEXT,
    created_seq BIGSERIAL
);

ALTER TABLE playlists ADD COLUMN IF NOT EXISTS owner_id TEXT;

CREATE TABLE IF NOT EXISTS songs (
    playlist_id TEXT NOT NULL REFERENCES playlists (id) ON DELETE CASCADE,
    position INTEGER NOT NULL CHECK (position >= 1),
    song_id TEXT NOT NULL,
    prev_id TEXT,
    next_id TEXT,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    source TEXT NOT NULL,
    duration DOUBLE PRECISION NOT NULL DEFAULT 0,
    album TEXT,
    artwork_url TEXT,
    external_url TEXT,
    available BOOLEAN NOT NULL DEFAULT TRUE,
    favorite BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (playlist_id, position)
);
"""

_INSERT_SONG = """
INSERT INTO songs (
    playlist_id, position, song_id, prev_id, next_id,
    title, artist, source, duration,
    album, artwork_url, external_url, available, favorite
) VALUES (
    %(playlist_id)s, %(position)s, %(song_id)s, %(prev_id)s, %(next_id)s,
    %(title)s, %(artist)s, %(source)s, %(duration)s,
    %(album)s, %(artwork_url)s, %(external_url)s, %(available)s, %(favorite)s
)
"""


def _optional_text(value: Any) -> str | None:
    """Normalise a nullable ``TEXT`` column to ``str | None``."""
    return None if value is None else str(value)


def _row_to_song(row: Mapping[str, Any]) -> Song:
    """Map one ``songs`` row back to the frozen :class:`Song` value."""
    return Song(
        id=str(row["song_id"]),
        title=str(row["title"]),
        artist=str(row["artist"]),
        source=AudioSourceType(str(row["source"])),
        duration=float(row["duration"]),
        album=_optional_text(row["album"]),
        artwork_url=_optional_text(row["artwork_url"]),
        external_url=_optional_text(row["external_url"]),
        available=bool(row["available"]),
        favorite=bool(row["favorite"]),
    )


class SqlPlaylistRepository(PlaylistRepository):
    """Database-backed repository; one short transaction per operation.

    Connections come from a small pool: opening a fresh TCP+TLS handshake to
    Neon on every request added hundreds of milliseconds to each call.
    """

    def __init__(self, dsn: str) -> None:
        """Create the connection pool and the schema on first use."""
        if not dsn.strip():
            raise ValueError("database DSN must not be empty")
        self._pool = ConnectionPool[psycopg.Connection[dict[str, Any]]](
            conninfo=dsn,
            min_size=0,
            max_size=5,
            kwargs={"row_factory": dict_row},
            name="playlists",
            open=True,
        )
        with self._connection() as connection:
            connection.execute(_SCHEMA)

    def close(self) -> None:
        """Shut the pool down (application shutdown, test teardown)."""
        self._pool.close()

    # ----------------------------------------------------------------- write

    def save(self, playlist: Playlist, *, owner_id: str | None = None) -> None:
        """Upsert the playlist and rewrite its songs as one transaction.

        Songs are immutable in place (``FEAT-001-b`` replaces the value), so a
        full rewrite of the child rows keeps ``position`` / ``prev_id`` /
        ``next_id`` consistent without per-row diffing — playlists are small
        and writes are user-driven.

        ``owner_id`` is written on insert and left alone afterwards, so an
        edit never re-homes a playlist to another device.
        """
        songs = playlist.to_list()
        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO playlists (id, name, owner_id)
                VALUES (%(id)s, %(name)s, %(owner_id)s)
                ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name
                """,
                {"id": playlist.id, "name": playlist.name, "owner_id": owner_id},
            )
            connection.execute(
                "DELETE FROM songs WHERE playlist_id = %(id)s",
                {"id": playlist.id},
            )
            for position, song in enumerate(songs, start=1):
                previous = songs[position - 2] if position > 1 else None
                following = songs[position] if position < len(songs) else None
                connection.execute(
                    _INSERT_SONG,
                    {
                        "playlist_id": playlist.id,
                        "position": position,
                        "song_id": song.id,
                        "prev_id": previous.id if previous else None,
                        "next_id": following.id if following else None,
                        "title": song.title,
                        "artist": song.artist,
                        "source": str(song.source),
                        "duration": song.duration,
                        "album": song.album,
                        "artwork_url": song.artwork_url,
                        "external_url": song.external_url,
                        "available": song.available,
                        "favorite": song.favorite,
                    },
                )

    def delete(self, playlist_id: str) -> bool:
        """Delete the playlist (songs cascade); ``False`` when absent."""
        with self._connection() as connection:
            cursor = connection.execute("DELETE FROM playlists WHERE id = %s", (playlist_id,))
            return cursor.rowcount > 0

    # ------------------------------------------------------------------ read

    def find_by_id(self, playlist_id: str) -> Playlist | None:
        """Return the playlist rebuilt from its rows, or ``None``."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT name FROM playlists WHERE id = %s", (playlist_id,)
            ).fetchone()
            if row is None:
                return None
            song_rows = connection.execute(
                """
                SELECT playlist_id, position, song_id, title, artist, source,
                       duration, album, artwork_url, external_url, available, favorite
                FROM songs WHERE playlist_id = %s ORDER BY position
                """,
                (playlist_id,),
            ).fetchall()
        # Rebuild: ordered rows -> Playlist appends head -> tail, re-linking.
        return Playlist(
            str(row["name"]),
            playlist_id=playlist_id,
            songs=[_row_to_song(song_row) for song_row in song_rows],
        )

    def list_all(self, *, owner_id: str | None = None) -> list[Playlist]:
        """Every playlist in insertion order with its songs.

        ``owner_id`` narrows the query to one device; ``None`` lists all.
        """
        with self._connection() as connection:
            if owner_id is None:
                playlist_rows = connection.execute(
                    "SELECT id, name FROM playlists ORDER BY created_seq"
                ).fetchall()
            else:
                playlist_rows = connection.execute(
                    """
                    SELECT id, name FROM playlists
                    WHERE owner_id = %(owner_id)s ORDER BY created_seq
                    """,
                    {"owner_id": owner_id},
                ).fetchall()
            song_rows = connection.execute(
                """
                SELECT playlist_id, position, song_id, title, artist, source,
                       duration, album, artwork_url, external_url, available, favorite
                FROM songs ORDER BY playlist_id, position
                """
            ).fetchall()

        grouped: dict[str, list[Song]] = defaultdict(list)
        for song_row in song_rows:
            grouped[str(song_row["playlist_id"])].append(_row_to_song(song_row))
        return [
            Playlist(
                str(row["name"]),
                playlist_id=str(row["id"]),
                songs=grouped.get(str(row["id"]), []),
            )
            for row in playlist_rows
        ]

    # ------------------------------------------------------------- internals

    @contextmanager
    def _connection(self) -> Iterator[psycopg.Connection[dict[str, Any]]]:
        """Yield a pooled connection: commit/rollback follow the block."""
        with self._pool.connection() as connection:
            yield connection


__all__ = ["SqlPlaylistRepository"]
