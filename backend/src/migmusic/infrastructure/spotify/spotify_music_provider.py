"""Maps Spotify payloads onto the domain :class:`Song`.

This is the only place that understands Spotify's JSON shape; if Spotify
renames a field, one function here changes and the whole app keeps working.

The access token is not a method parameter: the API edge sets it on the
request-scoped :data:`current_access_token` context variable, so the
:class:`MusicProvider` contract stays provider-agnostic (see the port).
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import Any

from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.domain.entities.song import Song
from migmusic.domain.ports.music_provider import MusicProvider
from migmusic.infrastructure.spotify.spotify_client import SpotifyApiClient

# Set per request by ``require_spotify_token``; read by the provider below.
current_access_token: ContextVar[str | None] = ContextVar("spotify_access_token", default=None)


def _require_token() -> str:
    """Return the request's Spotify token or fail loudly (programming error)."""
    token = current_access_token.get()
    if not token:
        raise RuntimeError("no Spotify access token in this request context")
    return token


class SpotifyMusicProvider(MusicProvider):
    """``MusicProvider`` backed by the Spotify Web API."""

    def __init__(self, client: SpotifyApiClient) -> None:
        self._client = client

    async def search_tracks(self, query: str, *, limit: int = 20) -> list[Song]:
        raw_items = await self._client.search_tracks(_require_token(), query, limit=limit)
        return _songs_from(raw_items)

    async def get_track(self, track_id: str) -> Song | None:
        raw = await self._client.track(_require_token(), track_id)
        track = _unwrap(raw)
        return _to_song(track) if track is not None else None

    # Spotify-only extras (not part of the generic port, but reachable through
    # the typed ``SpotifyProviderDep`` used by the Spotify router).

    async def saved_tracks(self, *, limit: int = 20) -> list[Song]:
        raw_items = await self._client.saved_tracks(_require_token(), limit=limit)
        return _songs_from(raw_items)

    async def playlist_tracks(self, playlist_id: str, *, limit: int = 50) -> list[Song]:
        raw_items = await self._client.playlist_tracks(_require_token(), playlist_id, limit=limit)
        return _songs_from(raw_items)


def _songs_from(items: list[Any]) -> list[Song]:
    """Convert a list of wrappers (``{track: ...}``) or bare tracks to songs."""
    songs: list[Song] = []
    for item in items:
        track = _unwrap(item)
        if track is None:
            continue
        song = _to_song(track)
        if song is not None:
            songs.append(song)
    return songs


def _unwrap(item: Any) -> dict[str, Any] | None:
    """Unwrap ``{track: {...}}`` / ``{item: {...}}`` envelopes; skip nulls."""
    if not isinstance(item, dict):
        return None
    if isinstance(item.get("track"), dict):
        inner: Any = item["track"]
        return inner if inner.get("id") else None
    if item.get("type") not in (None, "track"):
        return None  # episodes and audiobooks are not songs
    return item if item.get("id") else None


def _to_song(track: dict[str, Any]) -> Song | None:
    """Build a ``Song``; returns ``None`` when Spotify sent an unusable track."""
    title = str(track.get("name") or "").strip()
    if not title:
        return None

    artists = track.get("artists")
    entries = artists if isinstance(artists, list) else []
    artist = ", ".join(
        str(entry.get("name") or "").strip()
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("name") or "").strip()
    )

    album = track.get("album")
    album_name = str(album.get("name") or "").strip() if isinstance(album, dict) else None
    artwork_url = _image_url(album.get("images") if isinstance(album, dict) else None)

    external_urls = track.get("external_urls")
    external_url = None
    if isinstance(external_urls, dict):
        candidate = external_urls.get("spotify")
        if isinstance(candidate, str):
            external_url = candidate

    duration_ms = track.get("duration_ms")
    if isinstance(duration_ms, (int, float)):
        duration = max(0.0, float(duration_ms) / 1000.0)
    else:
        duration = 0.0

    return Song(
        id=str(track["id"]),
        title=title,
        artist=artist,
        source=AudioSourceType.SPOTIFY,
        duration=duration,
        album=album_name,
        artwork_url=artwork_url,
        external_url=external_url,
        available=track.get("is_playable") is not False,
    )


def _image_url(images: Any) -> str | None:
    if not isinstance(images, list) or not images:
        return None
    first = images[0]
    if isinstance(first, dict):
        url = first.get("url")
        if isinstance(url, str):
            return url
    return None


__all__ = ["SpotifyMusicProvider"]
