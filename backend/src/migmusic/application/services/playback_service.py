"""Transport use cases: which song plays, where the cursor sits, where we are.

The service is the single owner of playback state (``PLAYER-011``): the
frontend executes the audio and reports back, while repeat/shuffle/skip rules
are decided here so they can be unit-tested without a browser.

State is kept **per owner**: each device has its own active playlist, cursor,
position and playback order, so two users never share a queue. Every method
receives an ``owner_id`` and the matching context is created on first use.

Shuffle follows ``PLAYER-004 = b``: the doubly linked list is never reordered,
an auxiliary permutation records the playback order and the cursor is moved to
whatever song that order selects.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
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


@dataclass
class _PlaybackContext:
    """Everything the transport remembers for one owner (one device)."""

    playlist_id: str | None = None
    repeat: RepeatMode = RepeatMode.OFF
    shuffle: bool = False
    order: list[int] = field(default_factory=list)
    order_playlist_id: str | None = None
    order_index: int = 0
    position: float = 0.0
    playing: bool = False
    cursors: dict[str, int] = field(default_factory=dict)


class PlaybackService:
    """Playback use cases over the active playlist of each owner."""

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
        self._contexts: dict[str, _PlaybackContext] = {}

    @property
    def skip_seconds(self) -> float:
        """Configured step in seconds (read-only)."""
        return self._skip_seconds

    def _context(self, owner_id: str) -> _PlaybackContext:
        """Return (creating on first use) the transport context of ``owner_id``."""
        context = self._contexts.get(owner_id)
        if context is None:
            context = _PlaybackContext()
            self._contexts[owner_id] = context
        return context

    # ------------------------------------------------------------ selection

    def open(self, playlist_id: str, *, owner_id: str) -> PlaybackState:
        """Start playing ``playlist_id`` from its first song.

        An empty playlist opens in silence instead of raising, because a fresh
        playlist (``PLAYLIST-002``) legitimately has no songs yet.
        """
        context = self._context(owner_id)
        playlist = self._find(context, playlist_id, owner_id)
        if playlist.size == 0:
            context.playlist_id = playlist_id
            self._ensure_order(context, playlist)
            context.position = 0.0
            context.playing = False
            return self.state(owner_id=owner_id)
        return self.select(playlist_id, 0, owner_id=owner_id)

    def select(self, playlist_id: str, index: int, *, owner_id: str) -> PlaybackState:
        """Jump to ``index`` of ``playlist_id``, activating that playlist."""
        context = self._context(owner_id)
        playlist = self._find(context, playlist_id, owner_id)
        if not 0 <= index < playlist.size:
            raise InvalidPositionError(index, playlist.size)
        context.playlist_id = playlist_id
        self._ensure_order(context, playlist)
        context.order_index = context.order.index(index)
        playlist.move_to(index)
        self._remember_cursor(context, playlist)
        context.position = 0.0
        context.playing = True
        return self.state(owner_id=owner_id)

    # ----------------------------------------------------------- transport

    def state(self, *, owner_id: str) -> PlaybackState:
        """Snapshot of the owner's active playlist (raises when nothing is open)."""
        context = self._context(owner_id)
        playlist = self._active(context, owner_id)
        self._ensure_order(context, playlist)
        index = playlist.current_index
        size = playlist.size
        wrap = context.repeat is RepeatMode.ALL and size > 0
        at_first, at_last = self._edges(context, playlist, index)
        return PlaybackState(
            playlist_id=context.playlist_id,
            song=playlist.current,
            index=index,
            position=context.position,
            playing=context.playing,
            repeat=context.repeat,
            shuffle=context.shuffle,
            size=size,
            available_next=size > 0 and (not at_last or wrap),
            available_previous=size > 0 and (not at_first or wrap),
            next_index=self._next_index(context, playlist, index),
            previous_index=self._previous_index(context, playlist, index),
            skip_seconds=self._skip_seconds,
        )

    def next(self, *, owner_id: str) -> PlaybackState:
        """Manual skip forward; honours the boundaries of ``PLAYLIST-009 = A``."""
        return self._advance(owner_id=owner_id, honour_repeat_one=False)

    def advance_on_end(self, *, owner_id: str) -> PlaybackState:
        """Track finished (``PLAYER-003`` autoplay); ``repeat one`` replays here."""
        return self._advance(owner_id=owner_id, honour_repeat_one=True)

    def previous(self, *, owner_id: str) -> PlaybackState:
        """Step back through the list (or through the shuffle order)."""
        context = self._context(owner_id)
        playlist = self._require_song(context, owner_id)
        self._ensure_order(context, playlist)

        if context.shuffle:
            if context.order_index > 0:
                self._play_order_position(context, playlist, context.order_index - 1)
            elif context.repeat is RepeatMode.ALL:
                self._play_order_position(context, playlist, len(context.order) - 1)
            return self.state(owner_id=owner_id)

        if playlist.move_previous():
            self._sync_order_to_cursor(context, playlist)
            context.position = 0.0
            context.playing = True
        elif context.repeat is RepeatMode.ALL:
            playlist.move_to(playlist.size - 1)
            self._sync_order_to_cursor(context, playlist)
            context.position = 0.0
            context.playing = True
        return self.state(owner_id=owner_id)

    def skip(self, direction: SkipDirection, *, owner_id: str) -> PlaybackState:
        """Move exactly ``skip_seconds`` forward or backward (``PLAYER-001/002``).

        Backing up from ``position <= skip_seconds`` jumps to the previous song
        instead of going negative (``PLAYER-002a``).
        """
        context = self._context(owner_id)
        playlist = self._require_song(context, owner_id)
        if direction is SkipDirection.BACKWARD and context.position <= self._skip_seconds:
            before = playlist.current_index
            state = self.previous(owner_id=owner_id)
            if playlist.current_index == before:
                # Already at the head: there is no previous song, so rewind to 0:00.
                context.position = 0.0
                return self.state(owner_id=owner_id)
            return state

        delta = self._skip_seconds if direction is SkipDirection.FORWARD else -self._skip_seconds
        context.position = self._clamp_position(playlist, context.position + delta)
        return self.state(owner_id=owner_id)

    def seek(self, position: float, *, owner_id: str) -> PlaybackState:
        """Move the cursor inside the current song (``PLAYER-007``)."""
        context = self._context(owner_id)
        playlist = self._require_song(context, owner_id)
        duration = self._duration(playlist)
        if position < 0 or (duration > 0 and position > duration):
            upper = "duration" if duration <= 0 else f"{duration} seconds"
            raise ValidationError(f"seek position must be between 0 and {upper}")
        context.position = position
        return self.state(owner_id=owner_id)

    def report(
        self,
        *,
        owner_id: str,
        position: float | None = None,
        playing: bool | None = None,
    ) -> PlaybackState:
        """Accept the position/audio state the frontend observes (``PLAYER-011``)."""
        context = self._context(owner_id)
        playlist = self._require_song(context, owner_id)
        if position is not None:
            if position < 0:
                raise ValidationError("reported position must not be negative")
            context.position = self._clamp_position(playlist, position)
        if playing is not None:
            context.playing = playing
        return self.state(owner_id=owner_id)

    def set_modes(
        self,
        *,
        owner_id: str,
        repeat: RepeatMode | None = None,
        shuffle: bool | None = None,
    ) -> PlaybackState:
        """Switch repeat (``FEAT-001-d``) and shuffle (``PLAYER-004``)."""
        context = self._context(owner_id)
        playlist = self._active(context, owner_id)
        if repeat is not None:
            context.repeat = repeat
        if shuffle is not None and shuffle != context.shuffle:
            context.shuffle = shuffle
            context.order_playlist_id = None
            self._ensure_order(context, playlist)
        return self.state(owner_id=owner_id)

    # ----------------------------------------------------------- internals

    def _advance(self, *, owner_id: str, honour_repeat_one: bool) -> PlaybackState:
        """Move to the next song of the playback order, stopping at the edges."""
        context = self._context(owner_id)
        playlist = self._require_song(context, owner_id)
        self._ensure_order(context, playlist)

        if honour_repeat_one and context.repeat is RepeatMode.ONE:
            context.position = 0.0
            context.playing = True
            return self.state(owner_id=owner_id)

        if context.shuffle:
            if context.order_index + 1 < len(context.order):
                self._play_order_position(context, playlist, context.order_index + 1)
            elif context.repeat is RepeatMode.ALL:
                self._play_order_position(context, playlist, 0)
            else:
                context.playing = False
            return self.state(owner_id=owner_id)

        if playlist.move_next():
            self._sync_order_to_cursor(context, playlist)
            context.position = 0.0
            context.playing = True
        elif context.repeat is RepeatMode.ALL:
            playlist.move_to(0)
            self._sync_order_to_cursor(context, playlist)
            context.position = 0.0
            context.playing = True
        else:
            # PLAYLIST-009 = A: the list stops at the tail, it never loops.
            context.playing = False
        return self.state(owner_id=owner_id)

    def _require_song(self, context: _PlaybackContext, owner_id: str) -> Playlist:
        """Active playlist for an operation that needs at least one song."""
        playlist = self._active(context, owner_id)
        self._ensure_order(context, playlist)
        if playlist.size == 0:
            raise EmptyPlaylistError("the playlist has no songs")
        return playlist

    def _active(self, context: _PlaybackContext, owner_id: str) -> Playlist:
        """Active playlist, or the matching domain error."""
        if context.playlist_id is None:
            raise NoActivePlaybackError("no playlist is being played")
        return self._find(context, context.playlist_id, owner_id)

    def _find(self, context: _PlaybackContext, playlist_id: str, owner_id: str) -> Playlist:
        playlist = self._repository.find_by_id(playlist_id, owner_id=owner_id)
        if playlist is None:
            raise PlaylistNotFoundError(playlist_id)
        # The SQL adapter rebuilds the list on every read (ADR-004), so its
        # cursor always comes back at the head; restore ours before anyone reads.
        cursor = context.cursors.get(playlist_id)
        if cursor is not None and 0 <= cursor < playlist.size:
            playlist.move_to(cursor)
        return playlist

    def _remember_cursor(self, context: _PlaybackContext, playlist: Playlist) -> None:
        """Persist where the cursor sits so the next read starts there."""
        if playlist.current_index is not None:
            context.cursors[playlist.id] = playlist.current_index

    def _edges(
        self, context: _PlaybackContext, playlist: Playlist, index: int | None
    ) -> tuple[bool, bool]:
        """Whether the cursor sits at the head and at the tail of the play order."""
        if context.shuffle:
            return context.order_index <= 0, context.order_index >= len(context.order) - 1
        if index is None:
            return True, True
        return index <= 0, index >= playlist.size - 1

    def _next_index(
        self, context: _PlaybackContext, playlist: Playlist, index: int | None
    ) -> int | None:
        """Index ``next`` would select, mirroring ``_advance`` without mutating."""
        if playlist.size == 0 or index is None:
            return None
        if context.shuffle:
            if context.order_index + 1 < len(context.order):
                return context.order[context.order_index + 1]
            return context.order[0] if context.repeat is RepeatMode.ALL else None
        if index < playlist.size - 1:
            return index + 1
        return 0 if context.repeat is RepeatMode.ALL else None

    def _previous_index(
        self, context: _PlaybackContext, playlist: Playlist, index: int | None
    ) -> int | None:
        """Index ``previous`` would select, mirroring ``previous`` without mutating."""
        if playlist.size == 0 or index is None:
            return None
        if context.shuffle:
            if context.order_index > 0:
                return context.order[context.order_index - 1]
            return context.order[-1] if context.repeat is RepeatMode.ALL else None
        if index > 0:
            return index - 1
        return playlist.size - 1 if context.repeat is RepeatMode.ALL else None

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

    def _play_order_position(
        self, context: _PlaybackContext, playlist: Playlist, order_index: int
    ) -> None:
        """Select ``context.order[order_index]`` as the song being played."""
        context.order_index = order_index
        playlist.move_to(context.order[order_index])
        self._remember_cursor(context, playlist)
        context.position = 0.0
        context.playing = True

    def _sync_order_to_cursor(self, context: _PlaybackContext, playlist: Playlist) -> None:
        """Follow the list cursor back into the playback order (shuffle off)."""
        index = playlist.current_index
        context.order_index = index if index is not None else 0
        self._remember_cursor(context, playlist)

    def _ensure_order(self, context: _PlaybackContext, playlist: Playlist) -> None:
        """Rebuild the playback order when the playlist identity or size changed."""
        if context.order_playlist_id == playlist.id and len(context.order) == playlist.size:
            return
        self._rebuild_order(context, playlist)
        context.order_playlist_id = playlist.id

    def _rebuild_order(self, context: _PlaybackContext, playlist: Playlist) -> None:
        """Recreate the order keeping the song under the cursor first."""
        size = playlist.size
        if size == 0:
            context.order = []
            context.order_index = 0
            return
        current = playlist.current_index
        current = 0 if current is None else current
        if context.shuffle:
            others = [index for index in range(size) if index != current]
            self._rng.shuffle(others)
            context.order = [current, *others]
        else:
            context.order = list(range(size))
        context.order_index = context.order.index(current)


__all__ = ["DEFAULT_SKIP_SECONDS", "PlaybackService"]
