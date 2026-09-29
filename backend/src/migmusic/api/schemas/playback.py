"""Playback request/response models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from migmusic.api.schemas.playlist import SongOut
from migmusic.application.dto.playback import PlaybackState, RepeatMode, SkipDirection


class PlaybackOut(BaseModel):
    """Everything the frontend needs to render the transport bar."""

    model_config = ConfigDict(from_attributes=True)

    playlist_id: str | None
    song: SongOut | None
    index: int | None
    position: float
    playing: bool
    repeat: RepeatMode
    shuffle: bool
    size: int
    available_next: bool
    available_previous: bool
    skip_seconds: float

    @classmethod
    def from_state(cls, state: PlaybackState) -> PlaybackOut:
        """Project the application DTO onto the wire model."""
        return cls.model_validate(state)


class OpenRequest(BaseModel):
    """Body of ``POST /api/playback/open``."""

    playlist_id: str


class SkipRequest(BaseModel):
    """Body of ``POST /api/playback/skip``; the server owns the step size."""

    direction: SkipDirection


class SeekRequest(BaseModel):
    """Body of ``POST /api/playback/seek`` (``PLAYER-007``)."""

    position: float = Field(ge=0)


class ReportRequest(BaseModel):
    """Body of ``POST /api/playback/report`` (``PLAYER-011``)."""

    position: float | None = Field(default=None, ge=0)
    playing: bool | None = None


class ModeRequest(BaseModel):
    """Body of ``POST /api/playback/modes`` (``FEAT-001-d``, ``PLAYER-004``)."""

    repeat: RepeatMode | None = None
    shuffle: bool | None = None


__all__ = [
    "ModeRequest",
    "OpenRequest",
    "PlaybackOut",
    "ReportRequest",
    "SeekRequest",
    "SkipRequest",
]
