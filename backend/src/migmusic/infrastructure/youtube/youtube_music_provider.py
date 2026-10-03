"""Maps YouTube Music payloads onto the domain :class:`Song`.

This is the only place that understands YouTube Music's JSON shape. Audio is
never resolved here: playback happens in the browser through the official
YouTube IFrame player using the ``videoId`` carried by the song id.
"""

from __future__ import annotations

from typing import Any

from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.domain.entities.song import Song
from migmusic.domain.ports.music_provider import MusicProvider
from migmusic.infrastructure.youtube.ytmusic_client import YtMusicClient

# YouTube Music thumbnails come at several sizes; ask for a mid one so lists
# stay light (the frontend also lazy-loads).
_THUMBNAIL_PREFIX = "https://music.youtube.com/watch?v="


class YouTubeMusicProvider(MusicProvider):
    """``MusicProvider`` backed by the unofficial, keyless ``ytmusicapi``."""

    def __init__(self, client: YtMusicClient) -> None:
        self._client = client

    async def search_tracks(self, query: str, *, limit: int = 20) -> list[Song]:
        raw_items = await self._client.search(query, limit=limit)
        songs: list[Song] = []
        for item in raw_items:
            song = _to_song(item)
            if song is not None:
                songs.append(song)
        return songs

    async def get_track(self, track_id: str) -> Song | None:
        details = await self._client.get_song(track_id)
        if details is None:
            return None
        return _details_to_song(track_id, details)

    async def get_lyrics(self, track: Song) -> str | None:
        """Return the lyrics for a YouTube track, or ``None`` when unavailable."""
        return await self._client.get_lyrics(track.id)


def _to_song(item: dict[str, Any]) -> Song | None:
    """Map one search result to a ``Song``; ``None`` when unusable."""
    video_id = item.get("videoId")
    title = str(item.get("title") or "").strip()
    if not isinstance(video_id, str) or not video_id or not title:
        return None

    duration_raw = item.get("duration_seconds")
    duration = float(duration_raw) if isinstance(duration_raw, (int, float)) else 0.0

    return Song(
        id=video_id,
        title=title,
        artist=_artist_name(item.get("artists")),
        source=AudioSourceType.YOUTUBE,
        duration=max(0.0, duration),
        album=_album_name(item.get("album")),
        artwork_url=_thumbnail(item.get("thumbnails")),
        external_url=f"{_THUMBNAIL_PREFIX}{video_id}",
        available=True,
    )


def _details_to_song(video_id: str, details: dict[str, Any]) -> Song | None:
    """Map a ``get_song`` ``videoDetails`` block to a ``Song``."""
    title = str(details.get("title") or "").strip()
    if not title:
        return None
    length = details.get("lengthSeconds")
    duration = float(length) if isinstance(length, (int, str)) and str(length).isdigit() else 0.0
    return Song(
        id=video_id,
        title=title,
        artist=str(details.get("author") or "").strip(),
        source=AudioSourceType.YOUTUBE,
        duration=max(0.0, duration),
        album=None,
        artwork_url=_thumbnail(details.get("thumbnail")),
        external_url=f"{_THUMBNAIL_PREFIX}{video_id}",
        available=True,
    )


def _artist_name(artists: Any) -> str:
    """Join the artist names YouTube Music returns as a list of dicts."""
    if not isinstance(artists, list):
        return ""
    names = [
        str(entry.get("name") or "").strip()
        for entry in artists
        if isinstance(entry, dict) and str(entry.get("name") or "").strip()
    ]
    return ", ".join(names)


def _album_name(album: Any) -> str | None:
    if isinstance(album, dict):
        name = str(album.get("name") or "").strip()
        return name or None
    return None


def _thumbnail(thumbnails: Any) -> str | None:
    """Pick a mid-size thumbnail (≈226px) when present, else the last one."""
    if not isinstance(thumbnails, list) or not thumbnails:
        return None
    best: str | None = None
    for entry in thumbnails:
        if not isinstance(entry, dict):
            continue
        url = entry.get("url")
        if not isinstance(url, str):
            continue
        best = url
        width = entry.get("width")
        if isinstance(width, int) and width >= 200:
            return url
    return best


__all__ = ["YouTubeMusicProvider"]
