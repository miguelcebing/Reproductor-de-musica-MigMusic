"""Use cases over playlists: create, rename, delete and edit the track list.

The service owns the *rules* (load, mutate, persist) so routers stay thin and
``Playlist`` stays free of persistence concerns.
"""

from __future__ import annotations

from migmusic.domain.entities.playlist import Playlist
from migmusic.domain.entities.song import Song
from migmusic.domain.exceptions import InvalidPositionError, PlaylistNotFoundError
from migmusic.domain.ports.playlist_repository import PlaylistRepository


class PlaylistService:
    """Playlist use cases, backed by a :class:`PlaylistRepository` port."""

    def __init__(self, repository: PlaylistRepository) -> None:
        """Receive the port by constructor (DIP): never instantiate an adapter here."""
        self._repository = repository

    # ----------------------------------------------------------------- read

    def list(self) -> list[Playlist]:
        """All stored playlists (``PLAYLIST-001 = B`` allows several)."""
        return self._repository.list_all()

    def get(self, playlist_id: str) -> Playlist:
        """One playlist, or a :class:`PlaylistNotFoundError` (HTTP 404)."""
        playlist = self._repository.find_by_id(playlist_id)
        if playlist is None:
            raise PlaylistNotFoundError(playlist_id)
        return playlist

    # --------------------------------------------------------------- write

    def create(self, name: str) -> Playlist:
        """Create and persist an empty playlist (``PLAYLIST-002``)."""
        playlist = Playlist(name)
        self._repository.save(playlist)
        return playlist

    def rename(self, playlist_id: str, name: str) -> Playlist:
        """Rename a playlist (``PLAYLIST-003``)."""
        playlist = self.get(playlist_id)
        playlist.rename(name)
        self._repository.save(playlist)
        return playlist

    def delete(self, playlist_id: str) -> None:
        """Delete a playlist; raises when it does not exist."""
        if not self._repository.delete(playlist_id):
            raise PlaylistNotFoundError(playlist_id)

    def add_song(self, playlist_id: str, song: Song, *, index: int | None = None) -> Playlist:
        """Append a song, or insert it at ``index`` when given (``UX-003``)."""
        playlist = self.get(playlist_id)
        if index is None:
            playlist.add(song)
        else:
            playlist.insert_at(index, song)
        self._repository.save(playlist)
        return playlist

    def remove_song(self, playlist_id: str, index: int) -> Song:
        """Remove the song at ``index`` and return it (``PLAYLIST-009b``)."""
        playlist = self.get(playlist_id)
        song = playlist.remove_at(index)
        self._repository.save(playlist)
        return song

    def move_song(self, playlist_id: str, from_index: int, to_index: int) -> Playlist:
        """Reorder by ``remove_at`` + ``insert_at`` (``FEAT-001-e``, both O(n)).

        Both bounds are validated *before* mutating, so a rejected request never
        leaves the playlist half-reordered.
        """
        playlist = self.get(playlist_id)
        if from_index == to_index:
            return playlist
        self._check_move(playlist, from_index, to_index)
        song = playlist.remove_at(from_index)
        playlist.insert_at(to_index, song)
        self._repository.save(playlist)
        return playlist

    # ----------------------------------------------------------- internals

    @staticmethod
    def _check_move(playlist: Playlist, from_index: int, to_index: int) -> None:
        """Validate ``from_index`` and the resulting ``to_index`` against current bounds."""
        if not 0 <= from_index < playlist.size:
            raise InvalidPositionError(from_index, playlist.size)
        # After removing one song the list holds size - 1 items to insert into.
        if not 0 <= to_index <= playlist.size - 1:
            raise InvalidPositionError(to_index, playlist.size - 1)


__all__ = ["PlaylistService"]
