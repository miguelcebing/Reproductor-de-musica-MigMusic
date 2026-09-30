"""Spotify catalog and playback endpoints.

Thin controllers: every call resolves a fresh access token (``SpotifyTokenDep``)
and forwards to the adapter. Tokens, ``Retry-After`` and 401 handling all stay
behind the ports, so no router talks to Spotify's JSON directly.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query, Response, status

from migmusic.api.dependencies import MusicProviderDep, SpotifyClientDep, SpotifyTokenDep
from migmusic.api.schemas import (
    DeviceRequest,
    PlayerStateOut,
    PlayRequest,
    SongOut,
    SpotifyPlaylistOut,
    SpotifySeekRequest,
    VolumeRequest,
    song_out,
)

router = APIRouter(prefix="/api/spotify", tags=["spotify"])


# --- Catalog ---------------------------------------------------------------


@router.get("/search", summary="Search tracks on Spotify")
async def search(
    token: SpotifyTokenDep,
    provider: MusicProviderDep,
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[SongOut]:
    """Return matching tracks already mapped to the domain song shape."""
    songs = await provider.search_tracks(token, q, limit=limit)
    return [song_out(song) for song in songs]


@router.get("/saved", summary="Tracks saved to the Spotify library")
async def saved(
    token: SpotifyTokenDep,
    provider: MusicProviderDep,
    limit: int = Query(default=20, ge=1, le=50),
) -> list[SongOut]:
    """Return the user's saved tracks (``user-library-read``)."""
    songs = await provider.saved_tracks(token, limit=limit)
    return [song_out(song) for song in songs]


@router.get("/playlists", summary="List the user's Spotify playlists")
async def playlists(
    token: SpotifyTokenDep,
    client: SpotifyClientDep,
    limit: int = Query(default=20, ge=1, le=50),
) -> list[SpotifyPlaylistOut]:
    """Return playlist headers; tracks are fetched on demand."""
    summaries = await client.list_playlists(token, limit=limit)
    return [
        SpotifyPlaylistOut(
            id=item.id,
            name=item.name,
            track_count=item.track_count,
            artwork_url=item.artwork_url,
        )
        for item in summaries
    ]


@router.get("/playlists/{playlist_id}/tracks", summary="Tracks of a Spotify playlist")
async def playlist_tracks(
    playlist_id: str,
    token: SpotifyTokenDep,
    provider: MusicProviderDep,
    limit: int = Query(default=50, ge=1, le=100),
) -> list[SongOut]:
    """Return the playlist's tracks mapped to songs."""
    songs = await provider.playlist_tracks(token, playlist_id, limit=limit)
    return [song_out(song) for song in songs]


# --- Player (Web Playback SDK backend proxy) --------------------------------


@router.put("/player/play", status_code=status.HTTP_204_NO_CONTENT, summary="Play or resume")
async def play(
    body: PlayRequest,
    token: SpotifyTokenDep,
    client: SpotifyClientDep,
) -> Response:
    """Start playback of ``uris`` (or resume) on the active device."""
    await client.start_playback(
        token,
        device_id=body.device_id,
        uris=body.uris,
        position_ms=body.position_ms,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/player/pause", status_code=status.HTTP_204_NO_CONTENT, summary="Pause")
async def pause(
    token: SpotifyTokenDep,
    client: SpotifyClientDep,
    body: DeviceRequest | None = None,
) -> Response:
    """Pause playback on the active device."""
    await client.pause_playback(token, device_id=_device(body))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/player/next", status_code=status.HTTP_204_NO_CONTENT, summary="Next track")
async def next_track(
    token: SpotifyTokenDep,
    client: SpotifyClientDep,
    body: DeviceRequest | None = None,
) -> Response:
    """Skip to the next track."""
    await client.next_track(token, device_id=_device(body))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/player/previous", status_code=status.HTTP_204_NO_CONTENT, summary="Previous track")
async def previous_track(
    token: SpotifyTokenDep,
    client: SpotifyClientDep,
    body: DeviceRequest | None = None,
) -> Response:
    """Skip to the previous track."""
    await client.previous_track(token, device_id=_device(body))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/player/seek", status_code=status.HTTP_204_NO_CONTENT, summary="Seek")
async def seek(
    body: SpotifySeekRequest,
    token: SpotifyTokenDep,
    client: SpotifyClientDep,
) -> Response:
    """Move the playhead to ``position_ms``."""
    await client.seek(token, body.position_ms, device_id=body.device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/player/volume", status_code=status.HTTP_204_NO_CONTENT, summary="Volume")
async def volume(
    body: VolumeRequest,
    token: SpotifyTokenDep,
    client: SpotifyClientDep,
) -> Response:
    """Set the playback volume (0-100)."""
    await client.set_volume(token, body.volume_percent, device_id=body.device_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/player/state", summary="Current Spotify playback state")
async def player_state(
    token: SpotifyTokenDep,
    client: SpotifyClientDep,
) -> PlayerStateOut:
    """Return a simplified state; ``404`` upstream means nothing is playing."""
    raw = await client.playback_state(token)
    return _state_out(raw)


def _device(body: DeviceRequest | None) -> str | None:
    """Read the optional device id from an optional body."""
    return body.device_id if body is not None else None


def _state_out(raw: dict[str, Any] | None) -> PlayerStateOut:
    """Flatten Spotify's nested playback object onto the wire model."""
    if not raw:
        return PlayerStateOut(playing=False)

    device = raw.get("device") if isinstance(raw.get("device"), dict) else None
    item = raw.get("item") if isinstance(raw.get("item"), dict) else None
    uri = item.get("uri") if item else None

    return PlayerStateOut(
        playing=bool(raw.get("is_playing")),
        position_ms=max(0, int(raw.get("progress_ms") or 0)),
        duration_ms=max(0, int(item.get("duration_ms") or 0)) if item else 0,
        track_uri=uri if isinstance(uri, str) else None,
        volume_percent=(device or {}).get("volume_percent"),
        device_id=(device or {}).get("id"),
    )
