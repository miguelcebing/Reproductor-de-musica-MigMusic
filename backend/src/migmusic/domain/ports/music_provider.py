"""Port for third-party music catalogs (Spotify, YouTube Music, ...).

Implementations live in ``infrastructure/<provider>``; only the mapping to the
domain :class:`~migmusic.domain.entities.song.Song` is part of the contract, so
the rest of the system never sees a raw provider payload.

The contract is deliberately **token-agnostic**: a provider that needs a
session (Spotify) resolves it from a request-scoped context set by the API
edge, while a keyless provider (YouTube Music) ignores it. That keeps the port
satisfiable by any source without leaking provider-specific parameters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from migmusic.domain.entities.song import Song


class MusicProvider(ABC):
    """Read-only access to a remote catalog, already mapped to ``Song``."""

    @abstractmethod
    async def search_tracks(self, query: str, *, limit: int = 20) -> list[Song]:
        """Search the catalog and return at most ``limit`` songs."""

    @abstractmethod
    async def get_track(self, track_id: str) -> Song | None:
        """Return one track by its provider id, or ``None`` when unknown."""

    async def get_lyrics(self, track: Song) -> str | None:
        """Return the plain-text lyrics for ``track`` when the source has them.

        Default implementation: sources without lyrics (Spotify, local) answer
        ``None`` so the caller can fall back to another service. Providers that
        can fetch lyrics (YouTube Music) override this.
        """
        return None
