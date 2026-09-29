"""Playlist: a named collection backed by a real doubly linked list.

Composition (not inheritance): the playlist owns a :class:`DoublyLinkedList` and
adds its own rules — identity, naming, and the operations the UI exposes. The
list stays the only place where links are manipulated.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from uuid import uuid4

from migmusic.core import ValidationError
from migmusic.domain.entities.song import Song
from migmusic.domain.structures.doubly_linked_list import DoublyLinkedList

_MAX_NAME_LENGTH = 120


class Playlist:
    """An ordered, mutable playlist identified by a UUID.

    Duplicates are allowed (no decision forbids them), so the same song may be
    queued twice; ``find`` always returns the first occurrence.
    """

    __slots__ = ("_id", "_name", "_songs")

    def __init__(
        self, name: str, *, playlist_id: str | None = None, songs: Iterable[Song] = ()
    ) -> None:
        """Create a playlist with an optional id and an optional set of songs.

        Args:
            name: Display name; trimmed and validated as non-empty.
            playlist_id: Explicit UUID; generated when omitted.
            songs: Songs appended in order (``O(n)``).
        """
        self._id = playlist_id or str(uuid4())
        self._name = self._validate_name(name)
        self._songs: DoublyLinkedList[Song] = DoublyLinkedList()
        for song in songs:
            self._songs.insert_at_end(song)

    # ------------------------------------------------------------------ data

    @property
    def id(self) -> str:
        """Stable UUID used by the API and the database (read-only)."""
        return self._id

    @property
    def name(self) -> str:
        """Display name (read-only; use :meth:`rename` to change it)."""
        return self._name

    @property
    def songs(self) -> DoublyLinkedList[Song]:
        """The underlying list (read-only reference, never replaced)."""
        return self._songs

    def rename(self, name: str) -> None:
        """Change the display name (``PLAYLIST-003``) — O(1)."""
        self._name = self._validate_name(name)

    # -------------------------------------------------------------- playback

    @property
    def current(self) -> Song | None:
        """Song under the cursor, or ``None`` when empty."""
        return self._songs.get_current()

    @property
    def size(self) -> int:
        """Number of songs — O(1)."""
        return self._songs.size

    def move_next(self) -> bool:
        """Advance the cursor; ``False`` at the tail (``PLAYLIST-009 = A``)."""
        return self._songs.move_next()

    def move_previous(self) -> bool:
        """Move the cursor back; ``False`` at the head (``PLAYLIST-009 = A``)."""
        return self._songs.move_previous()

    def move_to(self, index: int) -> Song:
        """Select a song by index from the UI — O(n)."""
        return self._songs.move_to(index)

    # ------------------------------------------------------------- mutation

    def add(self, song: Song) -> None:
        """Append a song — O(1)."""
        self._songs.insert_at_end(song)

    def insert_at(self, index: int, song: Song) -> None:
        """Insert a song at ``index`` (drag & drop uses this) — O(n)."""
        self._songs.insert_at(index, song)

    def remove_at(self, index: int) -> Song:
        """Remove and return the song at ``index`` — O(n)."""
        return self._songs.remove_at(index)

    def find(self, song: Song) -> int | None:
        """Index of ``song``, or ``None`` (``PLAYLIST-008``, ``FEAT-001-c``) — O(n)."""
        return self._songs.find(song)

    def find_by(self, predicate: Callable[[Song], bool]) -> int | None:
        """Index of the first song matching ``predicate`` — O(n)."""
        return self._songs.find_by(predicate)

    # --------------------------------------------------------------- display

    def to_list(self) -> list[Song]:
        """Snapshot for DTOs and the didactic view — O(n)."""
        return self._songs.to_list()

    def __iter__(self) -> Iterator[Song]:
        """Iterate head → tail."""
        return iter(self._songs)

    def __len__(self) -> int:
        """Number of songs."""
        return self._songs.size

    def __contains__(self, song: object) -> bool:
        """Membership test by value."""
        return song in self._songs

    def __repr__(self) -> str:
        """Readable summary, e.g. ``Playlist('Road trip', size=12)``."""
        return f"{type(self).__name__}({self._name!r}, size={self.size})"

    # ------------------------------------------------------------- internals

    @staticmethod
    def _validate_name(name: str) -> str:
        """Trim and validate a playlist name."""
        cleaned = name.strip()
        if not cleaned:
            raise ValidationError("playlist name must not be empty")
        if len(cleaned) > _MAX_NAME_LENGTH:
            raise ValidationError(f"playlist name must be at most {_MAX_NAME_LENGTH} characters")
        return cleaned
