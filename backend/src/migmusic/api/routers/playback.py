"""Transport endpoints: next, previous, seek, skip, modes and position reports."""

from __future__ import annotations

from fastapi import APIRouter

from migmusic.api.dependencies import PlaybackServiceDep
from migmusic.api.schemas import (
    ModeRequest,
    OpenRequest,
    PlaybackOut,
    ReportRequest,
    SeekRequest,
    SkipRequest,
)

router = APIRouter(prefix="/api/playback", tags=["playback"])


@router.get("", summary="Current playback state", response_model=PlaybackOut)
def get_state(service: PlaybackServiceDep) -> PlaybackOut:
    """State of the active playlist (404 before the first ``open``)."""
    return PlaybackOut.from_state(service.state())


@router.post("/open", summary="Start playing a playlist", response_model=PlaybackOut)
def open_playlist(body: OpenRequest, service: PlaybackServiceDep) -> PlaybackOut:
    """Open a playlist from its first song (silence when it is empty)."""
    return PlaybackOut.from_state(service.open(body.playlist_id))


@router.post("/next", summary="Next song", response_model=PlaybackOut)
def next_song(service: PlaybackServiceDep) -> PlaybackOut:
    """Manual skip forward; stops at the tail (``PLAYLIST-009 = A``)."""
    return PlaybackOut.from_state(service.next())


@router.post("/previous", summary="Previous song", response_model=PlaybackOut)
def previous_song(service: PlaybackServiceDep) -> PlaybackOut:
    """Step back; stops at the head (``PLAYLIST-009 = A``)."""
    return PlaybackOut.from_state(service.previous())


@router.post("/finished", summary="Current song ended", response_model=PlaybackOut)
def song_finished(service: PlaybackServiceDep) -> PlaybackOut:
    """Autoplay hook (``PLAYER-003``); honours repeat one (``FEAT-001-d``)."""
    return PlaybackOut.from_state(service.advance_on_end())


@router.post("/skip", summary="Skip the configured number of seconds")
def skip(body: SkipRequest, service: PlaybackServiceDep) -> PlaybackOut:
    """Move ``PLAYER-001/002`` seconds; backwards near 0 goes to the previous song."""
    return PlaybackOut.from_state(service.skip(body.direction))


@router.post("/seek", summary="Jump inside the current song", response_model=PlaybackOut)
def seek(body: SeekRequest, service: PlaybackServiceDep) -> PlaybackOut:
    """Set the position (``PLAYER-007``); out-of-range values return 422."""
    return PlaybackOut.from_state(service.seek(body.position))


@router.post("/report", summary="Report observed position and audio state")
def report(body: ReportRequest, service: PlaybackServiceDep) -> PlaybackOut:
    """Frontend → backend position sync (``PLAYER-011``)."""
    return PlaybackOut.from_state(service.report(position=body.position, playing=body.playing))


@router.post("/modes", summary="Set repeat and shuffle", response_model=PlaybackOut)
def set_modes(body: ModeRequest, service: PlaybackServiceDep) -> PlaybackOut:
    """Switch repeat (``FEAT-001-d``) and shuffle (``PLAYER-004``)."""
    return PlaybackOut.from_state(service.set_modes(repeat=body.repeat, shuffle=body.shuffle))
