"""Transport endpoints: next, previous, seek, skip, modes and position reports.

Every route requires ``X-Device-Id``; the transport context is per owner, so
each device drives its own queue.
"""

from __future__ import annotations

from fastapi import APIRouter

from migmusic.api.dependencies import DeviceIdDep, PlaybackServiceDep
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
def get_state(service: PlaybackServiceDep, owner_id: DeviceIdDep) -> PlaybackOut:
    """State of the caller's active playlist (404 before the first ``open``)."""
    return PlaybackOut.from_state(service.state(owner_id=owner_id))


@router.post("/open", summary="Start playing a playlist", response_model=PlaybackOut)
def open_playlist(
    body: OpenRequest, service: PlaybackServiceDep, owner_id: DeviceIdDep
) -> PlaybackOut:
    """Open a playlist from its first song (silence when it is empty)."""
    return PlaybackOut.from_state(service.open(body.playlist_id, owner_id=owner_id))


@router.post("/next", summary="Next song", response_model=PlaybackOut)
def next_song(service: PlaybackServiceDep, owner_id: DeviceIdDep) -> PlaybackOut:
    """Manual skip forward; stops at the tail (``PLAYLIST-009 = A``)."""
    return PlaybackOut.from_state(service.next(owner_id=owner_id))


@router.post("/previous", summary="Previous song", response_model=PlaybackOut)
def previous_song(service: PlaybackServiceDep, owner_id: DeviceIdDep) -> PlaybackOut:
    """Step back; stops at the head (``PLAYLIST-009 = A``)."""
    return PlaybackOut.from_state(service.previous(owner_id=owner_id))


@router.post("/finished", summary="Current song ended", response_model=PlaybackOut)
def song_finished(service: PlaybackServiceDep, owner_id: DeviceIdDep) -> PlaybackOut:
    """Autoplay hook (``PLAYER-003``); honours repeat one (``FEAT-001-d``)."""
    return PlaybackOut.from_state(service.advance_on_end(owner_id=owner_id))


@router.post("/skip", summary="Skip the configured number of seconds")
def skip(body: SkipRequest, service: PlaybackServiceDep, owner_id: DeviceIdDep) -> PlaybackOut:
    """Move ``PLAYER-001/002`` seconds; backwards near 0 goes to the previous song."""
    return PlaybackOut.from_state(service.skip(body.direction, owner_id=owner_id))


@router.post("/seek", summary="Jump inside the current song", response_model=PlaybackOut)
def seek(body: SeekRequest, service: PlaybackServiceDep, owner_id: DeviceIdDep) -> PlaybackOut:
    """Set the position (``PLAYER-007``); out-of-range values return 422."""
    return PlaybackOut.from_state(service.seek(body.position, owner_id=owner_id))


@router.post("/report", summary="Report observed position and audio state")
def report(body: ReportRequest, service: PlaybackServiceDep, owner_id: DeviceIdDep) -> PlaybackOut:
    """Frontend → backend position sync (``PLAYER-011``)."""
    return PlaybackOut.from_state(
        service.report(owner_id=owner_id, position=body.position, playing=body.playing)
    )


@router.post("/modes", summary="Set repeat and shuffle", response_model=PlaybackOut)
def set_modes(body: ModeRequest, service: PlaybackServiceDep, owner_id: DeviceIdDep) -> PlaybackOut:
    """Switch repeat (``FEAT-001-d``) and shuffle (``PLAYER-004``)."""
    return PlaybackOut.from_state(
        service.set_modes(owner_id=owner_id, repeat=body.repeat, shuffle=body.shuffle)
    )
