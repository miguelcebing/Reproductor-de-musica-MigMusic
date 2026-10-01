"""Use cases over playlists: create, rename, delete and edit the track list.

The service owns the *rules* (load, mutate, persist) so routers stay thin and
``Playlist`` stays free of persistence concerns.
"""

from __future__ import annotations

from migmusic.core import ValidationError
from migmusic.domain.entities.playlist import Playlist
from migmusic.domain.entities.song import Song
from migmusic.domain.exceptions import (
    InvalidPositionError,
    ItemNotFoundError,
    PlaylistNotFoundError,
)
from migmusic.domain.ports.playlist_repository import PlaylistRepository


class PlaylistService:
    """Playlist use cases, backed by a :class:`PlaylistRepository` port."""

    def __init__(self, repository: PlaylistRepository) -> None:
        """Receive the port by constructor (DIP): never instantiate an adapter here."""
        self._repository = repository

    # ----------------------------------------------------------------- read

    def list(self, *, owner_id: str | None = None) -> list[Playlist]:
        """Stored playlists (``PLAYLIST-001 = B`` allows several).

        ``owner_id`` scopes the answer to one device; ``None`` lists every
        playlist, which is what the tooling and smoke checks rely on.
        """
        return self._repository.list_all(owner_id=owner_id)

    def get(self, playlist_id: str) -> Playlist:
        """One playlist, or a :class:`PlaylistNotFoundError` (HTTP 404)."""
        playlist = self._repository.find_by_id(playlist_id)
        if playlist is None:
            raise PlaylistNotFoundError(playlist_id)
        return playlist

    # --------------------------------------------------------------- write

    def create(self, name: str, *, owner_id: str | None = None) -> Playlist:
        """Create and persist an empty playlist (``PLAYLIST-002``).

        ``owner_id`` stamps the device that asked for it, so later lists from
        other devices never see it (UX isolation, not authentication).
        """
        playlist = Playlist(name)
        self._repository.save(playlist, owner_id=owner_id)
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

    def set_favorite(self, playlist_id: str, index: int, favorite: bool) -> Song:
        """Persist the heart flag of one song (``FEAT-001-b``)."""
        playlist = self.get(playlist_id)
        song = playlist.set_favorite(index, favorite)
        self._repository.save(playlist)
        return song

    def find_song(self, playlist_id: str, text: str) -> tuple[int, Song]:
        """First song whose title or artist contains ``text`` (``FEAT-001-c``).

        Runs ``find_by`` over the doubly linked list — O(n), first match wins,
        and the cursor is never moved (searching must not change playback).
        """
        cleaned = text.strip()
        if not cleaned:
            raise ValidationError("search text must not be empty")
        playlist = self.get(playlist_id)
        needle = cleaned.casefold()
        index = playlist.find_by(
            lambda song: needle in song.title.casefold() or needle in song.artist.casefold()
        )
        if index is None:
            raise ItemNotFoundError(f"no song matches {cleaned!r}")
        return index, playlist.song_at(index)

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
