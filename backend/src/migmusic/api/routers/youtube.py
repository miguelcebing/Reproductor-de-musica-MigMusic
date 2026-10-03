"""YouTube Music catalog endpoints (metadata only, keyless).

Audio playback is done in the browser by the official YouTube IFrame player;
the backend only serves search results mapped to the domain song shape.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from migmusic.api.dependencies import MusicProviderRegistryDep
from migmusic.api.schemas import SongOut, song_out
from migmusic.domain.entities.audio_source import AudioSourceType

router = APIRouter(prefix="/api/youtube", tags=["youtube"])


@router.get("/search", summary="Search songs on YouTube Music")
async def search(
    registry: MusicProviderRegistryDep,
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
) -> list[SongOut]:
    """Return matching tracks already mapped to the domain song shape."""
    provider = registry.get(AudioSourceType.YOUTUBE)
    songs = await provider.search_tracks(q, limit=limit)
    return [song_out(song) for song in songs]
