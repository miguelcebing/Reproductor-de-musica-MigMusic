"""Playback vocabulary shared by ``PlaybackService`` and the API edge.

``RepeatMode`` is the policy from ``FEAT-001-d``, ``SkipDirection`` the step
requested by ``PLAYER-001/002`` and ``PlaybackState`` the single answer the
frontend receives from every transport endpoint, so routers never assemble
payloads themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from migmusic.domain.entities.song import Song


class RepeatMode(StrEnum):
    """How the player behaves when the last (or first) track ends."""

    OFF = "off"
    ONE = "one"
    ALL = "all"


class SkipDirection(StrEnum):
    """Which way the ``PLAYER-001/002`` step of ``skip_seconds`` moves."""

    FORWARD = "forward"
    BACKWARD = "backward"


@dataclass(frozen=True, slots=True)
class PlaybackState:
    """Snapshot of the active playlist as the frontend should render it.

    Attributes:
        playlist_id: Playlist being played, ``None`` before the first open.
        song: Song under the cursor, ``None`` when the playlist is empty.
        index: Its index in list order (``None`` when there is no song).
        position: Current position in seconds.
        playing: Whether audio should be sounding right now.
        repeat: Repeat policy (``FEAT-001-d``).
        shuffle: Whether the playback order is a permutation (``PLAYER-004``).
        size: Number of songs in the playlist.
        available_next: ``False`` at the tail (``PLAYLIST-009 = A``).
        available_previous: ``False`` at the head (``PLAYLIST-009 = A``).
        skip_seconds: Configured ``PLAYER-001/002`` step.
    """

    playlist_id: str | None
    song: Song | None
    index: int | None
    position: float
    playing: bool
    repeat: RepeatMode
    shuffle: bool
    size: int
    available_next: bool
    available_previous: bool
    skip_seconds: float
