"""Playlist endpoints.

Thin controllers: translate HTTP to a service call and the result to a schema.
No try/except — ``error_handlers.py`` owns the mapping to status codes.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from migmusic.api.dependencies import PlaybackServiceDep, PlaylistServiceDep
from migmusic.api.schemas import (
    PlaybackOut,
    PlaylistCreate,
    PlaylistOut,
    PlaylistRename,
    SongCreate,
    SongMove,
    SongOut,
    song_out,
)

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


@router.get("", summary="List every playlist")
def list_playlists(service: PlaylistServiceDep) -> list[PlaylistOut]:
    """Return all stored playlists with their songs in list order."""
    return [PlaylistOut.from_entity(playlist) for playlist in service.list()]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a playlist")
def create_playlist(body: PlaylistCreate, service: PlaylistServiceDep) -> PlaylistOut:
    """Create an empty playlist (``PLAYLIST-002``)."""
    return PlaylistOut.from_entity(service.create(body.name))


@router.get("/{playlist_id}", summary="Read one playlist")
def get_playlist(playlist_id: str, service: PlaylistServiceDep) -> PlaylistOut:
    """Return a single playlist (404 when the id is unknown)."""
    return PlaylistOut.from_entity(service.get(playlist_id))


@router.patch("/{playlist_id}", summary="Rename a playlist")
def rename_playlist(
    playlist_id: str, body: PlaylistRename, service: PlaylistServiceDep
) -> PlaylistOut:
    """Rename a playlist (``PLAYLIST-003``)."""
    return PlaylistOut.from_entity(service.rename(playlist_id, body.name))


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete")
def delete_playlist(playlist_id: str, service: PlaylistServiceDep) -> Response:
    """Delete a playlist; answers ``204`` with an empty body."""
    service.delete(playlist_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{playlist_id}/songs",
    status_code=status.HTTP_201_CREATED,
    summary="Append or insert a song",
)
def add_song(playlist_id: str, body: SongCreate, service: PlaylistServiceDep) -> PlaylistOut:
    """Add a song at the end, or at ``index`` when provided (``UX-003``)."""
    playlist = service.add_song(
        playlist_id,
        song=body.song.to_entity(),
        index=body.index,
    )
    return PlaylistOut.from_entity(playlist)


@router.delete("/{playlist_id}/songs/{index}", summary="Remove a song")
def remove_song(playlist_id: str, index: int, service: PlaylistServiceDep) -> SongOut:
    """Remove the song at ``index`` (``PLAYLIST-009b`` fixes the cursor)."""
    return song_out(service.remove_song(playlist_id, index))


@router.put("/{playlist_id}/songs/order", summary="Reorder songs")
def move_song(playlist_id: str, body: SongMove, service: PlaylistServiceDep) -> PlaylistOut:
    """Move one song to another position (``FEAT-001-e``)."""
    playlist = service.move_song(playlist_id, body.from_index, body.to_index)
    return PlaylistOut.from_entity(playlist)


@router.post(
    "/{playlist_id}/songs/{index}/select",
    summary="Play a song",
    response_model=PlaybackOut,
)
def select_song(playlist_id: str, index: int, service: PlaybackServiceDep) -> PlaybackOut:
    """Activate the playlist, move the cursor and return the playback state."""
    return PlaybackOut.from_state(service.select(playlist_id, index))
