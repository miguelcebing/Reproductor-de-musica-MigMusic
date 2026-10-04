"""Port for lyrics sources.

A lyrics provider looks up a song by its metadata (title/artist) and returns
the :class:`~migmusic.domain.entities.lyrics.Lyrics` or ``None`` when it has
no match. Implementations live in ``infrastructure/lyrics`` and never leak
their HTTP shape to the domain.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from migmusic.domain.entities.lyrics import Lyrics


class LyricsProvider(ABC):
    """Look up lyrics for a track that has none of its own."""

    @abstractmethod
    async def find(self, *, title: str, artist: str, duration: float = 0.0) -> Lyrics | None:
        """Return the lyrics for a title/artist pair, or ``None`` on a miss."""


__all__ = ["LyricsProvider"]
