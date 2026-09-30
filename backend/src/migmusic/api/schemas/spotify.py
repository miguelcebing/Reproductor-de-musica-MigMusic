"""Spotify catalog and player request/response models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SpotifyPlaylistOut(BaseModel):
    """Header of a Spotify playlist (tracks are fetched separately)."""

    id: str
    name: str
    track_count: int
    artwork_url: str | None = None


class PlayRequest(BaseModel):
    """Body of ``PUT /api/spotify/player/play`` (SDK backend proxy)."""

    device_id: str | None = None
    uris: list[str] | None = None
    position_ms: int = Field(default=0, ge=0)


class DeviceRequest(BaseModel):
    """Body of the endpoints that only need a target device."""

    device_id: str | None = None


class SpotifySeekRequest(BaseModel):
    """Body of ``PUT /api/spotify/player/seek``."""

    position_ms: int = Field(ge=0)
    device_id: str | None = None


class VolumeRequest(BaseModel):
    """Body of ``PUT /api/spotify/player/volume``."""

    volume_percent: int = Field(ge=0, le=100)
    device_id: str | None = None


class PlayerStateOut(BaseModel):
    """Simplified playback state used to sync the UI with the SDK."""

    playing: bool
    position_ms: int = 0
    duration_ms: int = 0
    track_uri: str | None = None
    volume_percent: int | None = None
    device_id: str | None = None


__all__ = [
    "DeviceRequest",
    "PlayRequest",
    "PlayerStateOut",
    "SpotifyPlaylistOut",
    "SpotifySeekRequest",
    "VolumeRequest",
]
