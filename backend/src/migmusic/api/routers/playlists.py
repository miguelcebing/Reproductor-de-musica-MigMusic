"""Playlist endpoints.

Thin controllers: translate HTTP to a service call and the result to a schema.
No try/except — ``error_handlers.py`` owns the mapping to status codes.

Every route requires ``X-Device-Id`` and forwards it as ``owner_id``, so a
caller can only ever read or mutate its own playlists.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from migmusic.api.dependencies import DeviceIdDep, PlaybackServiceDep, PlaylistServiceDep
from migmusic.api.schemas import (
    PlaybackOut,
    PlaylistCreate,
    PlaylistOut,
    PlaylistRename,
    SongBatchCreate,
    SongCreate,
    SongFavorite,
    SongFound,
    SongMove,
    SongOut,
    song_out,
)

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


@router.get("", summary="List the caller's playlists")
def list_playlists(service: PlaylistServiceDep, owner_id: DeviceIdDep) -> list[PlaylistOut]:
    """Return the caller's playlists with their songs in list order."""
    return [PlaylistOut.from_entity(playlist) for playlist in service.list(owner_id=owner_id)]


@router.post("", status_code=status.HTTP_201_CREATED, summary="Create a playlist")
def create_playlist(
    body: PlaylistCreate, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> PlaylistOut:
    """Create an empty playlist (``PLAYLIST-002``) owned by the caller device."""
    return PlaylistOut.from_entity(service.create(body.name, owner_id=owner_id))


@router.get("/{playlist_id}", summary="Read one playlist")
def get_playlist(
    playlist_id: str, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> PlaylistOut:
    """Return one of the caller's playlists (404 when unknown or foreign)."""
    return PlaylistOut.from_entity(service.get(playlist_id, owner_id=owner_id))


@router.patch("/{playlist_id}", summary="Rename a playlist")
def rename_playlist(
    playlist_id: str, body: PlaylistRename, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> PlaylistOut:
    """Rename one of the caller's playlists (``PLAYLIST-003``)."""
    return PlaylistOut.from_entity(service.rename(playlist_id, body.name, owner_id=owner_id))


@router.delete("/{playlist_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete")
def delete_playlist(
    playlist_id: str, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> Response:
    """Delete one of the caller's playlists; answers ``204`` with an empty body."""
    service.delete(playlist_id, owner_id=owner_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{playlist_id}/songs",
    status_code=status.HTTP_201_CREATED,
    summary="Append or insert a song",
)
def add_song(
    playlist_id: str, body: SongCreate, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> PlaylistOut:
    """Add a song at the end, or at ``index`` when provided (``UX-003``)."""
    playlist = service.add_song(
        playlist_id,
        song=body.song.to_entity(),
        index=body.index,
        owner_id=owner_id,
    )
    return PlaylistOut.from_entity(playlist)


@router.post(
    "/{playlist_id}/songs/batch",
    status_code=status.HTTP_201_CREATED,
    summary="Append or insert several songs in one request",
)
def add_songs(
    playlist_id: str, body: SongBatchCreate, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> PlaylistOut:
    """Add a batch of songs with one read and one write (latency fix).

    Declared before ``/{playlist_id}/songs/{index}`` so ``batch`` is never
    parsed as a song index.
    """
    playlist = service.add_songs(
        playlist_id,
        [song.to_entity() for song in body.songs],
        index=body.index,
        owner_id=owner_id,
    )
    return PlaylistOut.from_entity(playlist)


@router.delete("/{playlist_id}/songs/{index}", summary="Remove a song")
def remove_song(
    playlist_id: str, index: int, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> SongOut:
    """Remove the song at ``index`` (``PLAYLIST-009b`` fixes the cursor)."""
    return song_out(service.remove_song(playlist_id, index, owner_id=owner_id))


@router.get("/{playlist_id}/songs/find", summary="Find a song by text")
def find_song(
    playlist_id: str, text: str, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> SongFound:
    """First title/artist match via the list's ``find_by`` (``FEAT-001-c``)."""
    index, song = service.find_song(playlist_id, text, owner_id=owner_id)
    return SongFound(index=index, song=song_out(song))


@router.put("/{playlist_id}/songs/{index}/favorite", summary="Mark a song as favourite")
def set_favorite(
    playlist_id: str,
    index: int,
    body: SongFavorite,
    service: PlaylistServiceDep,
    owner_id: DeviceIdDep,
) -> SongOut:
    """Set the heart flag of one song (``FEAT-001-b``)."""
    return song_out(service.set_favorite(playlist_id, index, body.favorite, owner_id=owner_id))


@router.put("/{playlist_id}/songs/order", summary="Reorder songs")
def move_song(
    playlist_id: str, body: SongMove, service: PlaylistServiceDep, owner_id: DeviceIdDep
) -> PlaylistOut:
    """Move one song to another position (``FEAT-001-e``)."""
    playlist = service.move_song(playlist_id, body.from_index, body.to_index, owner_id=owner_id)
    return PlaylistOut.from_entity(playlist)


@router.post(
    "/{playlist_id}/songs/{index}/select",
    summary="Play a song",
    response_model=PlaybackOut,
)
def select_song(
    playlist_id: str, index: int, service: PlaybackServiceDep, owner_id: DeviceIdDep
) -> PlaybackOut:
    """Activate the playlist, move the cursor and return the playback state."""
    return PlaybackOut.from_state(service.select(playlist_id, index, owner_id=owner_id))
