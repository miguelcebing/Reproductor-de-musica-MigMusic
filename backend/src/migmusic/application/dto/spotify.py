"""Spotify-specific DTOs (never exposed as domain entities)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SpotifyPlaylistSummary:
    """Header of a Spotify playlist: enough to list, not enough to play."""

    id: str
    name: str
    track_count: int
    artwork_url: str | None = None


__all__ = ["SpotifyPlaylistSummary"]
