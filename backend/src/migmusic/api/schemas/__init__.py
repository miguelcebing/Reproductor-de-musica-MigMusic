"""Request/response models. Pydantic models never appear in the domain layer."""

from migmusic.api.schemas.auth import (
    AccessTokenOut,
    AuthStatusOut,
    CallbackBody,
    CallbackOut,
)
from migmusic.api.schemas.lyrics import LyricsOut, LyricsQuery
from migmusic.api.schemas.playback import (
    ModeRequest,
    OpenRequest,
    PlaybackOut,
    ReportRequest,
    SeekRequest,
    SkipRequest,
)
from migmusic.api.schemas.playlist import (
    PlaylistCreate,
    PlaylistOut,
    PlaylistRename,
    SongBatchCreate,
    SongCreate,
    SongFavorite,
    SongFound,
    SongIn,
    SongMove,
    SongOut,
    song_out,
)
from migmusic.api.schemas.spotify import (
    DeviceRequest,
    PlayRequest,
    PlayerStateOut,
    SpotifyPlaylistOut,
    SpotifySeekRequest,
    VolumeRequest,
)

__all__ = [
    "AccessTokenOut",
    "AuthStatusOut",
    "CallbackBody",
    "CallbackOut",
    "DeviceRequest",
    "LyricsOut",
    "LyricsQuery",
    "ModeRequest",
    "OpenRequest",
    "PlayRequest",
    "PlaybackOut",
    "PlayerStateOut",
    "PlaylistCreate",
    "PlaylistOut",
    "PlaylistRename",
    "ReportRequest",
    "SeekRequest",
    "SkipRequest",
    "SongBatchCreate",
    "SongCreate",
    "SongFavorite",
    "SongFound",
    "SongIn",
    "SongMove",
    "SongOut",
    "SpotifyPlaylistOut",
    "SpotifySeekRequest",
    "VolumeRequest",
    "song_out",
]
