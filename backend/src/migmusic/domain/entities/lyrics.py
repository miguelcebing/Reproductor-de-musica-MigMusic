"""Lyrics value object returned by the lyrics services."""

from __future__ import annotations

from dataclasses import dataclass, field

from migmusic.core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class LyricLine:
    """One lyric line with the moment (seconds) it starts at."""

    time: float
    text: str


@dataclass(frozen=True, slots=True)
class Lyrics:
    """Lyrics for one track, optionally time-synced.

    Attributes:
        text: The full lyrics as plain text; never empty.
        source: Where the lyrics came from (``"youtube"``, ``"lrclib"``), so
            the UI can credit the provider.
        synced: Whether timed (LRC) lines were available. When ``True``,
            ``lines`` carries the timestamps the UI uses to scroll along.
        lines: Timed lines (empty when only plain text exists). ``text`` is
            always usable, so a client that ignores ``lines`` still works.
    """

    text: str
    source: str
    synced: bool = False
    lines: tuple[LyricLine, ...] = field(default=())

    def __post_init__(self) -> None:
        """Reject an empty body: a miss must be ``None``, not a blank object."""
        if not self.text.strip():
            raise ValidationError("Lyrics text must not be empty")

    def __str__(self) -> str:
        return f"{self.source}:{self.text[:40]}"


__all__ = ["LyricLine", "Lyrics"]
