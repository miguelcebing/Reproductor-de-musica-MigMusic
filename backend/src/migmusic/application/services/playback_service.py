"""Transport use cases: which song plays, where the cursor sits, where we are.

The service is the single owner of playback state (``PLAYER-011``): the
frontend executes the audio and reports back, while repeat/shuffle/skip rules
are decided here so they can be unit-tested without a browser.

Shuffle follows ``PLAYER-004 = b``: the doubly linked list is never reordered,
an auxiliary permutation records the playback order and the cursor is moved to
whatever song that order selects.
"""

from __future__ import annotations

import random
from typing import Final

from migmusic.application.dto.playback import PlaybackState, RepeatMode, SkipDirection
from migmusic.core import ValidationError
from migmusic.domain.entities.playlist import Playlist
from migmusic.domain.exceptions import (
    EmptyPlaylistError,
    InvalidPositionError,
    NoActivePlaybackError,
    PlaylistNotFoundError,
)
from migmusic.domain.ports.playlist_repository import PlaylistRepository

DEFAULT_SKIP_SECONDS: Final = 5.0
"""``PLAYER-001/002``: both buttons step exactly this many seconds."""


class PlaybackService:
    """Playback use cases over the active playlist."""

    def __init__(
        self,
        repository: PlaylistRepository,
        *,
        skip_seconds: float = DEFAULT_SKIP_SECONDS,
        rng: random.Random | None = None,
    ) -> None:
        """Receive the repository port by constructor (DIP).

        Args:
            repository: Where playlists live.
            skip_seconds: Configured ``PLAYER-001/002`` step.
            rng: Random source for shuffle; injectable so tests stay stable.
        """
        self._repository = repository
        self._skip_seconds = skip_seconds
        self._rng = rng if rng is not None else random.Random()  # noqa: S311
        self._playlist_id: str | None = None
        self._repeat = RepeatMode.OFF
        self._shuffle = False
        self._order: list[int] = []
        self._order_playlist_id: str | None = None
        self._order_index = 0
        self._position = 0.0
        self._playing = False
        self._cursors: dict[str, int] = {}

    @property
    def skip_seconds(self) -> float:
        """Configured step in seconds (read-only)."""
        return self._skip_seconds

    # ------------------------------------------------------------ selection

    def open(self, playlist_id: str) -> PlaybackState:
        """Start playing ``playlist_id`` from its first song.

        An empty playlist opens in silence instead of raising, because a fresh
        playlist (``PLAYLIST-002``) legitimately has no songs yet.
        """
        playlist = self._find(playlist_id)
        if playlist.size == 0:
            self._playlist_id = playlist_id
            self._ensure_order(playlist)
            self._position = 0.0
            self._playing = False
            return self.state()
        return self.select(playlist_id, 0)

    def select(self, playlist_id: str, index: int) -> PlaybackState:
        """Jump to ``index`` of ``playlist_id``, activating that playlist."""
        playlist = self._find(playlist_id)
        if not 0 <= index < playlist.size:
            raise InvalidPositionError(index, playlist.size)
        self._playlist_id = playlist_id
        self._ensure_order(playlist)
        self._order_index = self._order.index(index)
        playlist.move_to(index)
        self._remember_cursor(playlist)
        self._position = 0.0
        self._playing = True
        return self.state()

    # ----------------------------------------------------------- transport

    def state(self) -> PlaybackState:
        """Snapshot of the active playlist (raises when nothing is open)."""
        playlist = self._active()
        self._ensure_order(playlist)
        index = playlist.current_index
        size = playlist.size
        wrap = self._repeat is RepeatMode.ALL and size > 0
        at_first, at_last = self._edges(playlist, index)
        return PlaybackState(
            playlist_id=self._playlist_id,
            song=playlist.current,
            index=index,
            position=self._position,
            playing=self._playing,
            repeat=self._repeat,
            shuffle=self._shuffle,
            size=size,
            available_next=size > 0 and (not at_last or wrap),
            available_previous=size > 0 and (not at_first or wrap),
            next_index=self._next_index(playlist, index),
            previous_index=self._previous_index(playlist, index),
            skip_seconds=self._skip_seconds,
        )

    def next(self) -> PlaybackState:
        """Manual skip forward; honours the boundaries of ``PLAYLIST-009 = A``."""
        return self._advance(honour_repeat_one=False)

    def advance_on_end(self) -> PlaybackState:
        """Track finished (``PLAYER-003`` autoplay); ``repeat one`` replays here."""
        return self._advance(honour_repeat_one=True)

    def previous(self) -> PlaybackState:
        """Step back through the list (or through the shuffle order)."""
        playlist = self._require_song()
        self._ensure_order(playlist)

        if self._shuffle:
            if self._order_index > 0:
                self._play_order_position(playlist, self._order_index - 1)
            elif self._repeat is RepeatMode.ALL:
                self._play_order_position(playlist, len(self._order) - 1)
            return self.state()

        if playlist.move_previous():
            self._sync_order_to_cursor(playlist)
            self._position = 0.0
            self._playing = True
        elif self._repeat is RepeatMode.ALL:
            playlist.move_to(playlist.size - 1)
            self._sync_order_to_cursor(playlist)
            self._position = 0.0
            self._playing = True
        return self.state()

    def skip(self, direction: SkipDirection) -> PlaybackState:
        """Move exactly ``skip_seconds`` forward or backward (``PLAYER-001/002``).

        Backing up from ``position <= skip_seconds`` jumps to the previous song
        instead of going negative (``PLAYER-002a``).
        """
        playlist = self._require_song()
        if direction is SkipDirection.BACKWARD and self._position <= self._skip_seconds:
            before = playlist.current_index
            state = self.previous()
            if playlist.current_index == before:
                # Already at the head: there is no previous song, so rewind to 0:00.
                self._position = 0.0
                return self.state()
            return state

        delta = self._skip_seconds if direction is SkipDirection.FORWARD else -self._skip_seconds
        self._position = self._clamp_position(playlist, self._position + delta)
        return self.state()

    def seek(self, position: float) -> PlaybackState:
        """Move the cursor inside the current song (``PLAYER-007``)."""
        playlist = self._require_song()
        duration = self._duration(playlist)
        if position < 0 or (duration > 0 and position > duration):
            upper = "duration" if duration <= 0 else f"{duration} seconds"
            raise ValidationError(f"seek position must be between 0 and {upper}")
        self._position = position
        return self.state()

    def report(
        self, *, position: float | None = None, playing: bool | None = None
    ) -> PlaybackState:
        """Accept the position/audio state the frontend observes (``PLAYER-011``)."""
        playlist = self._require_song()
        if position is not None:
            if position < 0:
                raise ValidationError("reported position must not be negative")
            self._position = self._clamp_position(playlist, position)
        if playing is not None:
            self._playing = playing
        return self.state()

    def set_modes(
        self, *, repeat: RepeatMode | None = None, shuffle: bool | None = None
    ) -> PlaybackState:
        """Switch repeat (``FEAT-001-d``) and shuffle (``PLAYER-004``)."""
        playlist = self._active()
        if repeat is not None:
            self._repeat = repeat
        if shuffle is not None and shuffle != self._shuffle:
            self._shuffle = shuffle
            self._order_playlist_id = None
            self._ensure_order(playlist)
        return self.state()

    # ----------------------------------------------------------- internals

    def _advance(self, *, honour_repeat_one: bool) -> PlaybackState:
        """Move to the next song of the playback order, stopping at the edges."""
        playlist = self._require_song()
        self._ensure_order(playlist)

        if honour_repeat_one and self._repeat is RepeatMode.ONE:
            self._position = 0.0
            self._playing = True
            return self.state()

        if self._shuffle:
            if self._order_index + 1 < len(self._order):
                self._play_order_position(playlist, self._order_index + 1)
            elif self._repeat is RepeatMode.ALL:
                self._play_order_position(playlist, 0)
            else:
                self._playing = False
            return self.state()

        if playlist.move_next():
            self._sync_order_to_cursor(playlist)
            self._position = 0.0
            self._playing = True
        elif self._repeat is RepeatMode.ALL:
            playlist.move_to(0)
            self._sync_order_to_cursor(playlist)
            self._position = 0.0
            self._playing = True
        else:
            # PLAYLIST-009 = A: the list stops at the tail, it never loops.
            self._playing = False
        return self.state()

    def _require_song(self) -> Playlist:
        """Active playlist for an operation that needs at least one song."""
        playlist = self._active()
        self._ensure_order(playlist)
        if playlist.size == 0:
            raise EmptyPlaylistError("the playlist has no songs")
        return playlist

    def _active(self) -> Playlist:
        """Active playlist, or the matching domain error."""
        if self._playlist_id is None:
            raise NoActivePlaybackError("no playlist is being played")
        return self._find(self._playlist_id)

    def _find(self, playlist_id: str) -> Playlist:
        playlist = self._repository.find_by_id(playlist_id)
        if playlist is None:
            raise PlaylistNotFoundError(playlist_id)
        # The SQL adapter rebuilds the list on every read (ADR-004), so its
        # cursor always comes back at the head; restore ours before anyone reads.
        cursor = self._cursors.get(playlist_id)
        if cursor is not None and 0 <= cursor < playlist.size:
            playlist.move_to(cursor)
        return playlist

    def _remember_cursor(self, playlist: Playlist) -> None:
        """Persist where the cursor sits so the next read starts there."""
        if playlist.current_index is not None:
            self._cursors[playlist.id] = playlist.current_index

    def _edges(self, playlist: Playlist, index: int | None) -> tuple[bool, bool]:
        """Whether the cursor sits at the head and at the tail of the play order."""
        if self._shuffle:
            return self._order_index <= 0, self._order_index >= len(self._order) - 1
        if index is None:
            return True, True
        return index <= 0, index >= playlist.size - 1

    def _next_index(self, playlist: Playlist, index: int | None) -> int | None:
        """Index ``next`` would select, mirroring ``_advance`` without mutating."""
        if playlist.size == 0 or index is None:
            return None
        if self._shuffle:
            if self._order_index + 1 < len(self._order):
                return self._order[self._order_index + 1]
            return self._order[0] if self._repeat is RepeatMode.ALL else None
        if index < playlist.size - 1:
            return index + 1
        return 0 if self._repeat is RepeatMode.ALL else None

    def _previous_index(self, playlist: Playlist, index: int | None) -> int | None:
        """Index ``previous`` would select, mirroring ``previous`` without mutating."""
        if playlist.size == 0 or index is None:
            return None
        if self._shuffle:
            if self._order_index > 0:
                return self._order[self._order_index - 1]
            return self._order[-1] if self._repeat is RepeatMode.ALL else None
        if index > 0:
            return index - 1
        return playlist.size - 1 if self._repeat is RepeatMode.ALL else None

    def _duration(self, playlist: Playlist) -> float:
        song = playlist.current
        return song.duration if song is not None else 0.0

    def _clamp_position(self, playlist: Playlist, position: float) -> float:
        """Keep ``position`` inside ``0 .. duration`` (open-ended when unknown)."""
        if position < 0:  # pragma: no cover - defensive; every caller validates first
            return 0.0
        duration = self._duration(playlist)
        if duration > 0 and position > duration:
            return duration
        return position

    def _play_order_position(self, playlist: Playlist, order_index: int) -> None:
        """Select ``_order[order_index]`` as the song being played."""
        self._order_index = order_index
        playlist.move_to(self._order[order_index])
        self._remember_cursor(playlist)
        self._position = 0.0
        self._playing = True

    def _sync_order_to_cursor(self, playlist: Playlist) -> None:
        """Follow the list cursor back into the playback order (shuffle off)."""
        index = playlist.current_index
        self._order_index = index if index is not None else 0
        self._remember_cursor(playlist)

    def _ensure_order(self, playlist: Playlist) -> None:
        """Rebuild the playback order when the playlist identity or size changed."""
        if self._order_playlist_id == playlist.id and len(self._order) == playlist.size:
            return
        self._rebuild_order(playlist)
        self._order_playlist_id = playlist.id

    def _rebuild_order(self, playlist: Playlist) -> None:
        """Recreate the order keeping the song under the cursor first."""
        size = playlist.size
        if size == 0:
            self._order = []
            self._order_index = 0
            return
        current = playlist.current_index
        current = 0 if current is None else current
        if self._shuffle:
            others = [index for index in range(size) if index != current]
            self._rng.shuffle(others)
            self._order = [current, *others]
        else:
            self._order = list(range(size))
        self._order_index = self._order.index(current)


__all__ = ["DEFAULT_SKIP_SECONDS", "PlaybackService"]
