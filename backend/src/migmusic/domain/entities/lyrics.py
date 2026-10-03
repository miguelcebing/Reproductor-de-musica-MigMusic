"""Lyrics value object returned by the lyrics services."""

from __future__ import annotations

from dataclasses import dataclass

from migmusic.core.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class Lyrics:
    """Plain-text lyrics for one track.

    Attributes:
        text: The lyrics body; never empty (an empty result is ``None``).
        source: Where the lyrics came from (``"youtube"``, ``"lrclib"``), so
            the UI can credit the provider.
        synced: Whether timed (LRC) lyrics were available. The plain ``text``
            is always usable, so the UI can ignore this flag safely.
    """

    text: str
    source: str
    synced: bool = False

    def __post_init__(self) -> None:
        """Reject an empty body: a miss must be ``None``, not a blank object."""
        if not self.text.strip():
            raise ValidationError("Lyrics text must not be empty")

    def __str__(self) -> str:
        return f"{self.source}:{self.text[:40]}"


__all__ = ["Lyrics"]
