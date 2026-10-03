"""Tests for ``PlaybackService`` — the transport rules of the player."""

from __future__ import annotations

import random
from collections.abc import Callable

import pytest

from migmusic.application.dto import RepeatMode, SkipDirection
from migmusic.application.services import PlaybackService, PlaylistService
from migmusic.core import ValidationError
from migmusic.domain import (
    EmptyPlaylistError,
    InvalidPositionError,
    NoActivePlaybackError,
    Playlist,
    PlaylistNotFoundError,
    Song,
)
from migmusic.infrastructure.persistence import InMemoryPlaylistRepository


def test_state_before_any_open_raises(playback_service: PlaybackService) -> None:
    """There is no implicit playlist: the frontend must open one first."""
    with pytest.raises(NoActivePlaybackError):
        playback_service.state(owner_id=OWNER)


def test_open_unknown_playlist_raises(playback_service: PlaybackService) -> None:
    """404 for an unknown playlist id."""
    with pytest.raises(PlaylistNotFoundError):
        playback_service.open("missing", owner_id=OWNER)


def test_open_starts_on_the_first_song(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``open`` is deterministic: index 0, position 0, playing."""
    playlist = seed_playlist(count=3)

    state = playback_service.open(playlist.id, owner_id=OWNER)

    assert state.index == 0
    assert state.position == 0.0
    assert state.playing is True
    assert state.size == 3
    assert playlist.current_index == 0


def test_open_an_empty_playlist_stays_silent(
    playback_service: PlaybackService, repository: InMemoryPlaylistRepository
) -> None:
    """A brand new playlist (``PLAYLIST-002``) opens without raising."""
    empty = Playlist("Fresh")
    repository.save(empty, owner_id=OWNER)

    state = playback_service.open(empty.id, owner_id=OWNER)

    assert state.song is None
    assert state.index is None
    assert state.playing is False
    assert state.size == 0
    assert state.available_next is False


def test_next_walks_the_list_in_order(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """The cursor advances through the real nodes, one song at a time."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)

    assert playback_service.next(owner_id=OWNER).index == 1
    assert playback_service.next(owner_id=OWNER).index == 2


def test_next_stops_at_the_tail(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYLIST-009 = A``: no wrap-around, playback simply stops."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.next(owner_id=OWNER)
    playback_service.next(owner_id=OWNER)

    state = playback_service.next(owner_id=OWNER)

    assert state.index == 2
    assert state.playing is False
    assert state.available_next is False


def test_previous_stops_at_the_head(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYLIST-009 = A`` on the way back too."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)

    state = playback_service.previous(owner_id=OWNER)

    assert state.index == 0
    assert state.playing is True
    assert state.available_previous is False


def test_previous_walks_backwards(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Manual navigation mirrors ``next``."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.next(owner_id=OWNER)

    assert playback_service.previous(owner_id=OWNER).index == 0


def test_repeat_all_wraps_at_both_ends(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``FEAT-001-d``: the *service* wraps, the list itself never becomes circular."""
    playlist = seed_playlist(count=3)
    original = [song.id for song in playlist]
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, repeat=RepeatMode.ALL)
    playback_service.next(owner_id=OWNER)
    playback_service.next(owner_id=OWNER)

    assert playback_service.next(owner_id=OWNER).index == 0
    assert playback_service.previous(owner_id=OWNER).index == 2
    assert [song.id for song in playlist] == original


def test_manual_next_ignores_repeat_one(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """A user pressing "next" expects the next song, even under repeat one."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, repeat=RepeatMode.ONE)

    assert playback_service.next(owner_id=OWNER).index == 1


def test_track_end_replays_the_song_under_repeat_one(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYER-003`` + ``FEAT-001-d``: the song restarts instead of advancing."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, repeat=RepeatMode.ONE)
    playback_service.seek(150.0, owner_id=OWNER)

    state = playback_service.advance_on_end(owner_id=OWNER)

    assert state.index == 0
    assert state.position == 0.0
    assert state.playing is True


def test_track_end_advances_without_repeat_one(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYER-003``: autoplay calls ``moveNext`` through the service."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)

    assert playback_service.advance_on_end(owner_id=OWNER).index == 1


def test_track_end_stops_at_the_tail_without_repeat(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Autoplay respects ``PLAYLIST-009 = A`` as well."""
    playlist = seed_playlist(count=2)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.advance_on_end(owner_id=OWNER)

    state = playback_service.advance_on_end(owner_id=OWNER)

    assert state.index == 1
    assert state.playing is False


def test_transport_on_an_empty_playlist_raises(
    playback_service: PlaybackService, repository: InMemoryPlaylistRepository
) -> None:
    """There is nothing to advance when the list has no songs."""
    empty = Playlist("Fresh")
    repository.save(empty, owner_id=OWNER)
    playback_service.open(empty.id, owner_id=OWNER)

    with pytest.raises(EmptyPlaylistError):
        playback_service.next(owner_id=OWNER)


def test_select_jumps_to_an_index(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Clicking a row (``UX-003``) selects and starts that song."""
    playlist = seed_playlist(count=3)

    state = playback_service.select(playlist.id, 2, owner_id=OWNER)

    assert state.index == 2
    assert state.playing is True
    assert playlist.current_index == 2


def test_select_rejects_an_out_of_range_index(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Bounds come from the list, so the answer is 422."""
    playlist = seed_playlist(count=2)

    with pytest.raises(InvalidPositionError):
        playback_service.select(playlist.id, 9, owner_id=OWNER)


def test_select_activates_another_playlist(
    playback_service: PlaybackService,
    seed_playlist: Callable[..., Playlist],
    repository: InMemoryPlaylistRepository,
    make_song: Callable[..., Song],
) -> None:
    """Only one playlist plays at a time (``PLAYLIST-001 = B``)."""
    first = seed_playlist(name="First", count=3)
    second = Playlist("Second")
    second.add(make_song())
    repository.save(second, owner_id=OWNER)

    state = playback_service.select(second.id, 0, owner_id=OWNER)

    assert state.playlist_id == second.id
    assert state.playlist_id != first.id
    assert state.size == 1


def test_skip_forward_moves_exactly_the_configured_seconds(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYER-001``: the step is exact and comes from the service."""
    playlist = seed_playlist(count=2, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)

    assert playback_service.skip(SkipDirection.FORWARD, owner_id=OWNER).position == 5.0
    assert playback_service.skip(SkipDirection.FORWARD, owner_id=OWNER).position == 10.0


def test_skip_forward_is_clamped_to_the_duration(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Skipping never leaves the song."""
    playlist = seed_playlist(count=1, duration=8.0)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.seek(6.0, owner_id=OWNER)

    assert playback_service.skip(SkipDirection.FORWARD, owner_id=OWNER).position == 8.0


def test_skip_backward_from_zero_goes_to_the_previous_song(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYER-002a``: at ``<= 5 s`` the previous song wins over rewinding."""
    playlist = seed_playlist(count=3, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.next(owner_id=OWNER)

    state = playback_service.skip(SkipDirection.BACKWARD, owner_id=OWNER)

    assert state.index == 0
    assert state.position == 0.0


def test_skip_backward_inside_the_song_rewinds_five_seconds(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYER-002a``: past 5 s the step is applied in place."""
    playlist = seed_playlist(count=3, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.seek(30.0, owner_id=OWNER)

    assert playback_service.skip(SkipDirection.BACKWARD, owner_id=OWNER).position == 25.0
    assert playback_service.state(owner_id=OWNER).index == 0


def test_skip_backward_at_the_head_rewinds_to_zero(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """There is no previous song, so the position lands on 0:00."""
    playlist = seed_playlist(count=2, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.seek(3.0, owner_id=OWNER)

    state = playback_service.skip(SkipDirection.BACKWARD, owner_id=OWNER)

    assert state.index == 0
    assert state.position == 0.0


def test_seek_moves_inside_the_current_song(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYER-007``: the progress bar can jump anywhere valid."""
    playlist = seed_playlist(count=1, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)

    assert playback_service.seek(42.5, owner_id=OWNER).position == 42.5


def test_seek_rejects_a_negative_position(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Positions before the start of the song are 422."""
    playlist = seed_playlist(count=1, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)

    with pytest.raises(ValidationError):
        playback_service.seek(-1.0, owner_id=OWNER)


def test_seek_rejects_a_position_past_the_end(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Positions after the duration are 422."""
    playlist = seed_playlist(count=1, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)

    with pytest.raises(ValidationError):
        playback_service.seek(500.0, owner_id=OWNER)


def test_report_syncs_the_observed_position(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYER-011``: the backend tracks what the browser is doing."""
    playlist = seed_playlist(count=1, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)

    state = playback_service.report(owner_id=OWNER, position=77.0, playing=False)

    assert state.position == 77.0
    assert state.playing is False


def test_report_can_move_the_playing_flag_alone(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Pause/play reports arrive without a position (the clock keeps ticking)."""
    playlist = seed_playlist(count=1, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.seek(20.0, owner_id=OWNER)

    state = playback_service.report(owner_id=OWNER, playing=False)

    assert state.playing is False
    assert state.position == 20.0


def test_report_clamps_a_position_past_the_end(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """A lagging browser cannot push the state beyond the duration."""
    playlist = seed_playlist(count=1, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)

    assert playback_service.report(owner_id=OWNER, position=400.0).position == 180.0


def test_report_rejects_a_negative_position(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Negative time is nonsense and answers 422."""
    playlist = seed_playlist(count=1, duration=180.0)
    playback_service.open(playlist.id, owner_id=OWNER)

    with pytest.raises(ValidationError):
        playback_service.report(owner_id=OWNER, position=-5.0)


def test_shuffle_keeps_the_list_intact_and_visits_every_song_once(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """``PLAYER-004 = b``: an auxiliary order, never a reordered chain."""
    playlist = seed_playlist(count=5)
    original = [song.id for song in playlist]
    playback_service.open(playlist.id, owner_id=OWNER)

    playback_service.set_modes(owner_id=OWNER, shuffle=True)

    seen = [playback_service.state(owner_id=OWNER).index]
    for _ in range(6):
        state = playback_service.next(owner_id=OWNER)
        if not state.playing:
            break
        seen.append(state.index)

    assert sorted(seen) == [0, 1, 2, 3, 4]
    assert [song.id for song in playlist] == original
    assert playback_service.state(owner_id=OWNER).shuffle is True


def test_disabling_shuffle_restores_the_natural_order(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Turning shuffle off returns to sequential ``move_next`` navigation."""
    playlist = seed_playlist(count=5)
    original = [song.id for song in playlist]
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, shuffle=True)
    playback_service.next(owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, shuffle=False)
    before = playlist.current_index
    assert before is not None

    state = playback_service.next(owner_id=OWNER)

    assert state.shuffle is False
    assert state.index == before + 1
    assert playlist.current_index == before + 1
    assert [song.id for song in playlist] == original


def test_shuffle_previous_steps_back_through_the_permutation(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Under shuffle, "previous" undoes "next" instead of following the list."""
    playlist = seed_playlist(count=6)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, shuffle=True)
    first = playback_service.next(owner_id=OWNER).index

    state = playback_service.previous(owner_id=OWNER)

    assert state.index == 0
    assert first != 0


def test_shuffle_previous_stops_at_the_first_song_of_the_order(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Without repeat all the transport stays put at the start of the order."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, shuffle=True)

    state = playback_service.previous(owner_id=OWNER)

    assert state.index == 0
    assert state.playing is True


def test_shuffle_with_repeat_all_wraps_to_the_end(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Repeat all applies to the playback order, not to the chain."""
    playlist = seed_playlist(count=4)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, repeat=RepeatMode.ALL, shuffle=True)
    seen = [0]
    for _ in range(3):
        seen.append(playback_service.next(owner_id=OWNER).index)

    state = playback_service.next(owner_id=OWNER)

    assert state.index == 0
    assert state.playing is True

    # Going back from the first song of the order lands on its last one.
    assert playback_service.previous(owner_id=OWNER).index == seen[-1]


def test_edges_are_reported_to_the_ui(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """The frontend disables the buttons from ``available_next/previous``."""
    playlist = seed_playlist(count=2)
    state = playback_service.open(playlist.id, owner_id=OWNER)

    assert state.available_previous is False
    assert state.available_next is True

    playback_service.next(owner_id=OWNER)
    assert playback_service.state(owner_id=OWNER).available_next is False


def test_state_reports_where_the_transport_would_land(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """The optimistic UI needs the exact target of next/previous."""
    playlist = seed_playlist(count=3)
    state = playback_service.open(playlist.id, owner_id=OWNER)

    assert state.next_index == 1
    assert state.previous_index is None

    playback_service.next(owner_id=OWNER)
    state = playback_service.state(owner_id=OWNER)
    assert state.next_index == 2
    assert state.previous_index == 0

    playback_service.next(owner_id=OWNER)
    state = playback_service.state(owner_id=OWNER)
    assert state.next_index is None
    assert state.previous_index == 1


def test_state_indexes_wrap_with_repeat_all(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Repeat all turns both edges into real targets."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, repeat=RepeatMode.ALL)
    playback_service.next(owner_id=OWNER)
    playback_service.next(owner_id=OWNER)

    at_tail = playback_service.state(owner_id=OWNER)
    assert at_tail.index == 2
    assert at_tail.next_index == 0
    assert at_tail.previous_index == 1

    playback_service.previous(owner_id=OWNER)
    playback_service.previous(owner_id=OWNER)
    at_head = playback_service.state(owner_id=OWNER)
    assert at_head.index == 0
    assert at_head.previous_index == 2


def test_state_indexes_ignore_repeat_one(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """A manual press still means the next song under repeat one."""
    playlist = seed_playlist(count=3)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, repeat=RepeatMode.ONE)

    assert playback_service.state(owner_id=OWNER).next_index == 1


def test_shuffle_state_indexes_follow_the_playback_order(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """Under shuffle the prediction comes from the permutation, not the list."""
    playlist = seed_playlist(count=5)
    playback_service.open(playlist.id, owner_id=OWNER)
    playback_service.set_modes(owner_id=OWNER, shuffle=True)

    seen = [playback_service.state(owner_id=OWNER).index]
    for _ in range(4):
        predicted = playback_service.state(owner_id=OWNER).next_index
        assert predicted is not None
        landed = playback_service.next(owner_id=OWNER).index
        assert landed == predicted
        seen.append(landed)

    assert sorted(seen) == [0, 1, 2, 3, 4]
    assert playback_service.state(owner_id=OWNER).next_index is None


def test_empty_playlist_has_no_transport_targets(
    playback_service: PlaybackService, repository: InMemoryPlaylistRepository
) -> None:
    """An empty playlist offers nothing to jump to."""
    empty = Playlist("Fresh")
    repository.save(empty, owner_id=OWNER)

    state = playback_service.open(empty.id, owner_id=OWNER)

    assert state.next_index is None
    assert state.previous_index is None
    assert state.available_next is False
    assert state.available_previous is False


def test_state_after_the_playlist_was_deleted_raises(
    playback_service: PlaybackService,
    playlist_service: PlaylistService,
    seed_playlist: Callable[..., Playlist],
) -> None:
    """Deleting the playlist being played invalidates the transport."""
    playlist = seed_playlist(count=2)
    playback_service.open(playlist.id, owner_id=OWNER)

    playlist_service.delete(playlist.id, owner_id=OWNER)

    with pytest.raises(PlaylistNotFoundError):
        playback_service.next(owner_id=OWNER)


def test_skip_seconds_is_exposed_to_the_frontend(
    playback_service: PlaybackService, seed_playlist: Callable[..., Playlist]
) -> None:
    """The UI shows the configured ``PLAYER-001/002`` step."""
    playlist = seed_playlist(count=1)
    playback_service.open(playlist.id, owner_id=OWNER)

    state = playback_service.state(owner_id=OWNER)

    assert state.skip_seconds == playback_service.skip_seconds == 5.0


def test_shuffle_order_is_reproducible_with_a_seeded_rng(
    repository: InMemoryPlaylistRepository, seed_playlist: Callable[..., Playlist]
) -> None:
    """An injectable RNG keeps shuffle testable without losing randomness."""
    playlist = seed_playlist(count=7)
    order_a = _shuffle_order(repository, playlist)
    order_b = _shuffle_order(repository, playlist)

    assert order_a == order_b
    assert sorted(order_a) == list(range(7))
    assert order_a != list(range(7))


def _shuffle_order(repository: InMemoryPlaylistRepository, playlist: Playlist) -> list[int]:
    """Open, enable shuffle and record the whole playback order."""
    service = PlaybackService(repository, rng=random.Random(1234))
    service.open(playlist.id, owner_id=OWNER)
    service.set_modes(owner_id=OWNER, shuffle=True)
    order = [service.state(owner_id=OWNER).index]
    for _ in range(playlist.size - 1):
        order.append(service.next(owner_id=OWNER).index)
    return order


# ------------------------------------------------- cursor survives rebuilds
# The SQL adapter rebuilds the playlist on every read (ADR-004), which resets
# the DLL cursor to the head; these tests reproduce that with fresh copies so
# the bug (next snapped back to the first song) is visible outside Postgres.


OWNER = "device-a"


class _RebuildingRepository(InMemoryPlaylistRepository):
    """Like the SQL adapter: ``find_by_id`` returns a rebuilt copy each time."""

    def __init__(self, store: InMemoryPlaylistRepository) -> None:
        """Share another adapter's data while losing the DLL cursor on read."""
        self._items = store._items
        self._owners = store._owners
        self._lock = store._lock

    def find_by_id(self, playlist_id: str, *, owner_id: str) -> Playlist | None:
        playlist = super().find_by_id(playlist_id, owner_id=owner_id)
        if playlist is None:
            return None
        return Playlist(playlist.name, playlist_id=playlist.id, songs=playlist.to_list())


def _rebuilding_service(repository: InMemoryPlaylistRepository) -> PlaybackService:
    """Playback wired to a repository whose reads lose the DLL cursor."""
    return PlaybackService(_RebuildingRepository(repository), rng=random.Random(0))


def test_next_survives_a_repository_that_rebuilds_the_playlist(
    repository: InMemoryPlaylistRepository, seed_playlist: Callable[..., Playlist]
) -> None:
    """Walking forward must not snap back to the first song on every read."""
    playlist = seed_playlist(count=3)
    songs = playlist.to_list()
    service = _rebuilding_service(repository)
    service.open(playlist.id, owner_id=OWNER)

    first = service.next(owner_id=OWNER)
    second = service.next(owner_id=OWNER)

    assert first.index == 1 and first.song == songs[1]
    assert second.index == 2 and second.song == songs[2]


def test_report_after_next_keeps_the_new_song(
    repository: InMemoryPlaylistRepository, seed_playlist: Callable[..., Playlist]
) -> None:
    """The delayed player report used to revert playback to the first song."""
    playlist = seed_playlist(count=3)
    songs = playlist.to_list()
    service = _rebuilding_service(repository)
    service.open(playlist.id, owner_id=OWNER)
    service.next(owner_id=OWNER)

    state = service.report(owner_id=OWNER, position=1.5, playing=True)

    assert state.index == 1
    assert state.song == songs[1]
    assert state.position == 1.5


def test_previous_walks_backwards_across_rebuilds(
    repository: InMemoryPlaylistRepository, seed_playlist: Callable[..., Playlist]
) -> None:
    """Stepping back keeps its place instead of jumping to the head."""
    playlist = seed_playlist(count=3)
    service = _rebuilding_service(repository)
    service.open(playlist.id, owner_id=OWNER)
    service.next(owner_id=OWNER)
    service.next(owner_id=OWNER)

    assert service.previous(owner_id=OWNER).index == 1
    assert service.previous(owner_id=OWNER).index == 0
    assert service.previous(owner_id=OWNER).index == 0  # repeat off: stays at the head
    assert service.state(owner_id=OWNER).available_previous is False


def test_select_and_report_stay_on_the_selected_index(
    repository: InMemoryPlaylistRepository, seed_playlist: Callable[..., Playlist]
) -> None:
    """Clicking a song in the UI keeps that song across subsequent reads."""
    playlist = seed_playlist(count=3)
    songs = playlist.to_list()
    service = _rebuilding_service(repository)

    selected = service.select(playlist.id, 2, owner_id=OWNER)
    reported = service.report(owner_id=OWNER, position=10.0, playing=True)

    assert selected.index == 2 and selected.song == songs[2]
    assert reported.index == 2 and reported.song == songs[2]


def test_tail_edge_survives_rebuilds(
    repository: InMemoryPlaylistRepository, seed_playlist: Callable[..., Playlist]
) -> None:
    """The last song reports no next and refuses to advance after rebuilds."""
    playlist = seed_playlist(count=3)
    service = _rebuilding_service(repository)
    service.open(playlist.id, owner_id=OWNER)
    service.next(owner_id=OWNER)
    service.next(owner_id=OWNER)

    at_tail = service.state(owner_id=OWNER)
    stuck = service.next(owner_id=OWNER)

    assert at_tail.index == 2 and at_tail.available_next is False
    assert stuck.index == 2 and stuck.playing is False


def test_a_shrunk_playlist_falls_back_to_the_head(
    repository: InMemoryPlaylistRepository, seed_playlist: Callable[..., Playlist]
) -> None:
    """A stored cursor beyond the new size is ignored instead of raising."""
    playlist = seed_playlist(count=3)
    service = _rebuilding_service(repository)
    service.open(playlist.id, owner_id=OWNER)
    service.next(owner_id=OWNER)
    service.next(owner_id=OWNER)  # cursor sits at index 2
    songs = playlist.to_list()
    rebuilt = Playlist(playlist.name, playlist_id=playlist.id, songs=songs[:1])
    repository.save(rebuilt, owner_id=OWNER)

    state = service.state(owner_id=OWNER)

    assert state.size == 1
    assert state.index == 0


def test_shuffle_order_survives_rebuilds(
    repository: InMemoryPlaylistRepository, seed_playlist: Callable[..., Playlist]
) -> None:
    """The permutation keeps advancing through fresh copies of the playlist."""
    playlist = seed_playlist(count=5)
    service = _rebuilding_service(repository)
    service.open(playlist.id, owner_id=OWNER)
    service.set_modes(owner_id=OWNER, shuffle=True)

    order = [service.state(owner_id=OWNER).index]
    for _ in range(4):
        order.append(service.next(owner_id=OWNER).index)

    assert sorted(order) == list(range(5))
