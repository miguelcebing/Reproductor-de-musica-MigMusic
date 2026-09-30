"""Tests for the Spotify catalog and player endpoints (stubbed Web API)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient


def _track(track_id: str = "abc123", name: str = "Night Drive") -> dict[str, Any]:
    return {
        "id": track_id,
        "name": name,
        "duration_ms": 215_400,
        "artists": [{"name": "Kavinsky"}],
        "album": {"name": "OutRun", "images": [{"url": "https://i.scdn.co/image/cover"}]},
        "external_urls": {"spotify": f"https://open.spotify.com/track/{track_id}"},
        "is_playable": True,
    }


def test_search_requires_a_linked_session(spotify_client: TestClient) -> None:
    """Anonymous traffic never reaches Spotify."""
    response = spotify_client.get("/api/spotify/search", params={"q": "night"})

    assert response.status_code == 401


def test_search_returns_mapped_songs(linked_client: TestClient, spotify_stub: Any) -> None:
    """The payload comes back in the domain song shape, ready for the queue."""
    spotify_stub.search_items = [_track()]

    response = linked_client.get("/api/spotify/search", params={"q": "night", "limit": 5})

    assert response.status_code == 200
    songs = response.json()
    assert len(songs) == 1
    assert songs[0]["id"] == "abc123"
    assert songs[0]["source"] == "spotify"
    assert songs[0]["duration_label"] == "3:35"
    assert songs[0]["artwork_url"] == "https://i.scdn.co/image/cover"


def test_search_sends_the_access_token(linked_client: TestClient, spotify_stub: Any) -> None:
    """Every Web API call carries the session's bearer token."""
    linked_client.get("/api/spotify/search", params={"q": "night"})

    api_requests = [r for r in spotify_stub.requests if r.url.host == "api.spotify.com"]
    assert api_requests
    assert api_requests[0].headers["authorization"] == "Bearer access-token-1"


def test_search_rejects_an_empty_query(linked_client: TestClient) -> None:
    """A blank query is a request validation error, not an upstream call."""
    response = linked_client.get("/api/spotify/search", params={"q": ""})

    assert response.status_code == 422


def test_saved_tracks_are_returned(linked_client: TestClient, spotify_stub: Any) -> None:
    """Saved library items are unwrapped into songs."""
    spotify_stub.saved_items = [{"added_at": "2024-01-01", "track": _track()}]

    response = linked_client.get("/api/spotify/saved")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Night Drive"


def test_playlist_headers_are_returned(linked_client: TestClient, spotify_stub: Any) -> None:
    """The list view only needs ids, names and track counts."""
    spotify_stub.playlists_payload = {
        "items": [
            {
                "id": "pl-1",
                "name": "Focus",
                "tracks": {"total": 12},
                "images": [{"url": "https://i.scdn.co/image/pl"}],
            }
        ]
    }

    response = linked_client.get("/api/spotify/playlists")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "pl-1",
            "name": "Focus",
            "track_count": 12,
            "artwork_url": "https://i.scdn.co/image/pl",
        }
    ]


def test_playlist_tracks_are_returned(linked_client: TestClient, spotify_stub: Any) -> None:
    """Tracks of one playlist arrive mapped and ordered."""
    spotify_stub.playlist_track_items = [{"track": _track()}]

    response = linked_client.get("/api/spotify/playlists/pl-1/tracks")

    assert response.status_code == 200
    assert [song["id"] for song in response.json()] == ["abc123"]


def test_player_endpoints_answer_204(linked_client: TestClient, spotify_stub: Any) -> None:
    """Every transport action proxies to the Web API and answers 204."""
    cases = [
        ("PUT", "/api/spotify/player/play", {"uris": ["spotify:track:abc123"]}),
        ("PUT", "/api/spotify/player/pause", None),
        ("POST", "/api/spotify/player/next", None),
        ("POST", "/api/spotify/player/previous", None),
        ("PUT", "/api/spotify/player/seek", {"position_ms": 42_000}),
        ("PUT", "/api/spotify/player/volume", {"volume_percent": 55}),
    ]

    for method, path, body in cases:
        response = linked_client.request(method, path, json=body)
        assert response.status_code == 204, f"{method} {path} -> {response.text}"


def test_play_sends_the_device_and_uris(linked_client: TestClient, spotify_stub: Any) -> None:
    """The play call reaches Spotify with the requested context."""
    linked_client.put(
        "/api/spotify/player/play",
        json={"device_id": "dev-1", "uris": ["spotify:track:abc123"], "position_ms": 1000},
    )

    play_requests = [r for r in spotify_stub.requests if r.url.path.endswith("/me/player/play")]
    assert play_requests
    body = play_requests[0].content.decode()
    assert "spotify:track:abc123" in body
    assert "dev-1" in str(play_requests[0].url)


def test_player_state_maps_the_spotify_payload(
    linked_client: TestClient, spotify_stub: Any
) -> None:
    """The simplified state carries exactly what the UI needs."""
    spotify_stub.player_state = {
        "is_playing": True,
        "progress_ms": 12_000,
        "item": {"uri": "spotify:track:abc123", "duration_ms": 215_400},
        "device": {"id": "dev-1", "volume_percent": 70},
    }

    response = linked_client.get("/api/spotify/player/state")

    assert response.status_code == 200
    assert response.json() == {
        "playing": True,
        "position_ms": 12_000,
        "duration_ms": 215_400,
        "track_uri": "spotify:track:abc123",
        "volume_percent": 70,
        "device_id": "dev-1",
    }


def test_player_state_without_a_device_is_idle(
    linked_client: TestClient, spotify_stub: Any
) -> None:
    """Spotify's 404 (nothing playing) becomes a neutral state."""
    response = linked_client.get("/api/spotify/player/state")

    assert response.status_code == 200
    assert response.json()["playing"] is False


def test_upstream_errors_keep_their_status(linked_client: TestClient, spotify_stub: Any) -> None:
    """A 429 from Spotify is forwarded as 429, not swallowed."""
    spotify_stub.player_error_status = 429

    response = linked_client.get("/api/spotify/player/state")

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "upstream_error"
