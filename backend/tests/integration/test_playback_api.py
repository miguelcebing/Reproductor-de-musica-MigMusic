"""Tests for the playback (transport) endpoints."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

PlaylistPayload = dict[str, Any]
FilledPlaylist = Callable[..., PlaylistPayload]


def test_state_before_opening_a_playlist_returns_404(client: TestClient) -> None:
    """There is no implicit playlist."""
    response = client.get("/api/playback")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_open_starts_the_first_song(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """``open`` answers the full transport state."""
    payload = filled_playlist(count=3)

    response = client.post("/api/playback/open", json={"playlist_id": payload["id"]})

    assert response.status_code == 200
    body = response.json()
    assert body["index"] == 0
    assert body["playing"] is True
    assert body["position"] == 0.0
    assert body["size"] == 3
    assert body["skip_seconds"] == 5.0
    assert body["available_previous"] is False
    assert body["available_next"] is True


def test_open_unknown_playlist_returns_404(client: TestClient) -> None:
    """Opening nothing is a 404."""
    response = client.post("/api/playback/open", json={"playlist_id": "nope"})

    assert response.status_code == 404


def test_next_and_previous_walk_the_list(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """Transport controls drive the cursor through the real nodes."""
    payload = filled_playlist(count=3)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})

    assert client.post("/api/playback/next").json()["index"] == 1
    assert client.post("/api/playback/next").json()["index"] == 2
    assert client.post("/api/playback/previous").json()["index"] == 1


def test_next_stops_at_the_tail(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """``PLAYLIST-009 = A`` over HTTP: playback stops, nothing wraps."""
    payload = filled_playlist(count=2)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})
    client.post("/api/playback/next")

    body = client.post("/api/playback/next").json()

    assert body["index"] == 1
    assert body["playing"] is False
    assert body["available_next"] is False


def test_skip_forward_moves_five_seconds(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """``PLAYER-001``: the server owns the step size."""
    payload = filled_playlist(count=2)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})

    assert (
        client.post("/api/playback/skip", json={"direction": "forward"}).json()["position"] == 5.0
    )
    assert (
        client.post("/api/playback/skip", json={"direction": "forward"}).json()["position"] == 10.0
    )


def test_skip_backward_at_the_start_goes_to_the_previous_song(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """``PLAYER-002a``: at 0:00 the previous song wins."""
    payload = filled_playlist(count=3)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})
    client.post("/api/playback/next")

    body = client.post("/api/playback/skip", json={"direction": "backward"}).json()

    assert body["index"] == 0
    assert body["position"] == 0.0


def test_seek_jumps_inside_the_song(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """``PLAYER-007``: click and drag on the progress bar."""
    payload = filled_playlist(count=1, duration=180.0)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})

    body = client.post("/api/playback/seek", json={"position": 42.5}).json()

    assert body["position"] == 42.5


def test_seek_past_the_end_is_422(client: TestClient, filled_playlist: FilledPlaylist) -> None:
    """Positions outside the song are rejected."""
    payload = filled_playlist(count=1, duration=60.0)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})

    response = client.post("/api/playback/seek", json={"position": 400.0})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_seek_to_a_negative_position_is_rejected_by_the_schema(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """``Field(ge=0)`` stops impossible positions before they reach the domain."""
    payload = filled_playlist(count=1, duration=60.0)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})

    response = client.post("/api/playback/seek", json={"position": -10.0})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "request_validation_error"


def test_report_syncs_the_browser_position(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """``PLAYER-011``: the frontend reports what it observes."""
    payload = filled_playlist(count=1, duration=180.0)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})

    body = client.post("/api/playback/report", json={"position": 90.0, "playing": False}).json()

    assert body["position"] == 90.0
    assert body["playing"] is False


def test_modes_switch_repeat_and_shuffle(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """``FEAT-001-d`` and ``PLAYER-004`` are reachable over HTTP."""
    payload = filled_playlist(count=4)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})

    body = client.post("/api/playback/modes", json={"repeat": "all", "shuffle": True}).json()

    assert body["repeat"] == "all"
    assert body["shuffle"] is True


def test_finished_replays_under_repeat_one(
    client: TestClient, filled_playlist: FilledPlaylist
) -> None:
    """``PLAYER-003`` + ``FEAT-001-d``: the song restarts instead of advancing."""
    payload = filled_playlist(count=3)
    client.post("/api/playback/open", json={"playlist_id": payload["id"]})
    client.post("/api/playback/modes", json={"repeat": "one"})
    client.post("/api/playback/seek", json={"position": 100.0})

    body = client.post("/api/playback/finished").json()

    assert body["index"] == 0
    assert body["position"] == 0.0
    assert body["playing"] is True


def test_unknown_playback_route_returns_the_error_envelope(
    client: TestClient,
) -> None:
    """Unknown routes follow the same shape as domain errors."""
    response = client.post("/api/playback/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
