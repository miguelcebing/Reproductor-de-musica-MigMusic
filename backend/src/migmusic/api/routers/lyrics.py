"""Lyrics endpoint.

The frontend posts the current track's metadata and gets its lyrics (or a
friendly ``204`` when none are found). A lyrics miss is not an error: playback
must keep working, so the endpoint answers ``204`` instead of ``404``.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from migmusic.api.dependencies import LyricsServiceDep
from migmusic.api.schemas.lyrics import LyricsOut, LyricsQuery
from migmusic.domain.entities.song import Song

router = APIRouter(prefix="/api/lyrics", tags=["lyrics"])


@router.post("", response_model=LyricsOut, summary="Lyrics for a track")
async def get_lyrics(
    body: LyricsQuery, service: LyricsServiceDep, response: Response
) -> LyricsOut | Response:
    """Return the lyrics for the posted track, or ``204`` when none exist."""
    lyrics = await service.lyrics_for(_song_from(body))
    if lyrics is None:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return LyricsOut(text=lyrics.text, source=lyrics.source, synced=lyrics.synced)


def _song_from(body: LyricsQuery) -> Song:
    """Rebuild the minimal :class:`Song` the lyrics service needs."""
    title = body.title.strip()
    artist = body.artist.strip()
    # Local tracks carry a prefixed id (`local:<uuid>`); the service only needs
    # it for the cache key, so a blank id falls back to title+artist.
    song_id = body.track_id.strip() or f"{body.source.value}:{title}:{artist}"
    return Song(
        id=song_id,
        title=title or "Unknown",
        artist=artist,
        source=body.source,
        duration=max(0.0, body.duration),
    )
