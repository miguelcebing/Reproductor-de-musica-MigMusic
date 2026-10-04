"""Playlist request/response models (the only place Pydantic appears)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.domain.entities.playlist import Playlist
from migmusic.domain.entities.song import Song

# Upper bounds keep a crafted body from pushing huge strings into the store or
# the database; they are far above any real metadata value.
_MAX_TITLE = 300
_MAX_ARTIST = 300
_MAX_URL = 2048
_MAX_ID = 200


class SongIn(BaseModel):
    """Song payload sent by the client.

    Structural checks only: ``Song`` enforces the domain rules so a violation
    always surfaces as the same ``422 validation_error``.
    """

    id: str = Field(min_length=1, max_length=_MAX_ID)
    title: str = Field(min_length=1, max_length=_MAX_TITLE)
    artist: str = Field(default="", max_length=_MAX_ARTIST)
    source: AudioSourceType
    duration: float = Field(default=0.0, ge=0)
    album: str | None = Field(default=None, max_length=_MAX_TITLE)
    artwork_url: str | None = Field(default=None, max_length=_MAX_URL)
    external_url: str | None = Field(default=None, max_length=_MAX_URL)
    available: bool = True

    def to_entity(self) -> Song:
        """Build the immutable domain entity; domain rules stay authoritative."""
        return Song(**self.model_dump())


class SongOut(BaseModel):
    """Serialised song, including the computed ``m:ss`` label."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    artist: str
    source: AudioSourceType
    duration: float
    album: str | None
    artwork_url: str | None
    external_url: str | None
    available: bool
    favorite: bool
    duration_label: str


class PlaylistOut(BaseModel):
    """Serialised playlist with its songs in list order."""

    id: str
    name: str
    size: int
    current_index: int | None
    songs: list[SongOut]

    @classmethod
    def from_entity(cls, playlist: Playlist) -> PlaylistOut:
        """Project a domain aggregate onto the wire model."""
        return cls(
            id=playlist.id,
            name=playlist.name,
            size=playlist.size,
            current_index=playlist.current_index,
            songs=[SongOut.model_validate(song) for song in playlist],
        )


class PlaylistCreate(BaseModel):
    """Body of ``POST /api/playlists``."""

    name: str = Field(min_length=1, max_length=120)


class PlaylistRename(BaseModel):
    """Body of ``PATCH /api/playlists/{id}``."""

    name: str = Field(min_length=1, max_length=120)


class SongCreate(BaseModel):
    """Body of ``POST /api/playlists/{id}/songs``; ``index`` inserts mid-list."""

    song: SongIn
    index: int | None = Field(default=None, ge=0)


class SongBatchCreate(BaseModel):
    """Body of ``POST /api/playlists/{id}/songs/batch``: add many in one trip."""

    songs: list[SongIn] = Field(min_length=1, max_length=100)
    index: int | None = Field(default=None, ge=0)


class SongMove(BaseModel):
    """Body of ``PUT /api/playlists/{id}/songs/order`` (``FEAT-001-e``)."""

    from_index: int = Field(ge=0)
    to_index: int = Field(ge=0)


class SongFavorite(BaseModel):
    """Body of ``PUT /api/playlists/{id}/songs/{index}/favorite`` (``FEAT-001-b``)."""

    favorite: bool


class SongFound(BaseModel):
    """Answer of ``GET /api/playlists/{id}/songs/find`` (``FEAT-001-c``)."""

    index: int
    song: SongOut


def song_out(song: Song) -> SongOut:
    """Project one song onto the wire model."""
    return SongOut.model_validate(song)


__all__ = [
    "PlaylistCreate",
    "PlaylistOut",
    "PlaylistRename",
    "SongCreate",
    "SongFavorite",
    "SongFound",
    "SongIn",
    "SongMove",
    "SongOut",
    "song_out",
]
