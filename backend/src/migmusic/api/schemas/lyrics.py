"""Lyrics request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field

from migmusic.domain.entities.audio_source import AudioSourceType


class LyricsQuery(BaseModel):
    """Body of ``POST /api/lyrics``: the track to look up."""

    # Lengths mirror the playlist schema so a crafted body cannot push an
    # oversized string into the store or an external service.
    title: str = Field(min_length=1, max_length=300)
    artist: str = Field(default="", max_length=300)
    duration: float = Field(default=0.0, ge=0)
    source: AudioSourceType = AudioSourceType.LOCAL
    track_id: str = Field(default="", max_length=200)


class LyricsOut(BaseModel):
    """Serialised lyrics for a song."""

    text: str
    source: str
    synced: bool


__all__ = ["LyricsOut", "LyricsQuery"]
