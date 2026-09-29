"""Immutable description of one song.

``Song`` is a value object: two songs with the same attributes are
interchangeable, which is what lets ``DoublyLinkedList`` find by value.
"""

from __future__ import annotations

from dataclasses import dataclass

from migmusic.core import ValidationError
from migmusic.domain.entities.audio_source import AudioSourceType


@dataclass(frozen=True, slots=True)
class Song:
    """A track as the rest of the system sees it, regardless of its source.

    Attributes:
        id: Stable identifier (``local:<uuid>`` or the Spotify track id).
        title: Display title; never empty.
        artist: Display artist; may be empty for untitled local files.
        source: Which engine must play it.
        duration: Length in seconds. ``0.0`` when still unknown (lazy load).
        album: Album name, when the source provides one.
        artwork_url: Cover image URL, when the source provides one.
        external_url: Public link (Spotify track page, ``None`` for local files).
        available: ``False`` when a local file is missing after a reload
            (``LOCAL-006``: metadata persists, the file must be re-selected).
    """

    id: str
    title: str
    artist: str
    source: AudioSourceType
    duration: float = 0.0
    album: str | None = None
    artwork_url: str | None = None
    external_url: str | None = None
    available: bool = True

    def __post_init__(self) -> None:
        """Validate invariants at construction time (the object is immutable)."""
        if not self.id.strip():
            raise ValidationError("song id must not be empty")
        if not self.title.strip():
            raise ValidationError("song title must not be empty")
        if self.duration < 0:
            raise ValidationError(f"song duration must not be negative: {self.duration}")

    @property
    def duration_label(self) -> str:
        """``m:ss`` label used by the UI (``0:00`` when the duration is unknown)."""
        total = int(self.duration)
        return f"{total // 60}:{total % 60:02d}"
