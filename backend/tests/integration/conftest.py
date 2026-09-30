"""Fixtures shared by the HTTP-level tests.

Each test gets a fresh application (and therefore a fresh repository), so no
state leaks between cases. Spotify is always stubbed with ``httpx.MockTransport``:
the suite never talks to the real service (``SKILL3``).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from migmusic.api.spotify_session import SESSION_COOKIE
from migmusic.application.services.spotify_auth_service import SpotifyAuthService
from migmusic.core import Settings
from migmusic.core.session import sign
from migmusic.domain.ports.token_store import TokenBundle
from migmusic.infrastructure.spotify.spotify_client import SpotifyApiClient
from migmusic.infrastructure.spotify.spotify_music_provider import SpotifyMusicProvider
from migmusic.main import create_app

PlaylistPayload = dict[str, Any]
Handler = Callable[[httpx.Request], httpx.Response]


class SpotifyStub:
    """Configurable stand-in for both Spotify hosts.

    Routes by URL path so tests only describe the payload they care about.
    """

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.token_payload: dict[str, Any] = {
            "access_token": "access-token-1",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh-token-1",
            "scope": "streaming",
        }
        self.search_items: list[dict[str, Any]] = []
        self.saved_items: list[dict[str, Any]] = []
        self.playlist_track_items: list[dict[str, Any]] = []
        self.playlists_payload: dict[str, Any] = {"items": []}
        self.player_state: dict[str, Any] | None = None
        self.player_status = 204
        self.player_error_status: int | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        host = request.url.host
        path = request.url.path

        if host == "accounts.spotify.com":
            return httpx.Response(200, json=self.token_payload)
        if host != "api.spotify.com":
            return httpx.Response(404, json={"error": "unknown host"})

        if self.player_error_status is not None and path.startswith("/v1/me/player"):
            return httpx.Response(
                self.player_error_status,
                headers={"retry-after": "1"} if self.player_error_status == 429 else {},
                json={"error": {"status": self.player_error_status}},
            )
        if path == "/v1/search":
            return httpx.Response(200, json={"tracks": {"items": self.search_items}})
        if path == "/v1/me/tracks":
            return httpx.Response(200, json={"items": self.saved_items})
        if path == "/v1/me/playlists":
            return httpx.Response(200, json=self.playlists_payload)
        if path.endswith("/tracks"):
            return httpx.Response(200, json={"items": self.playlist_track_items})
        if path == "/v1/me/player":
            if self.player_state is None:
                return httpx.Response(404, json={"error": "no active device"})
            return httpx.Response(200, json=self.player_state)
        if path.startswith("/v1/me/player"):
            return httpx.Response(self.player_status)
        return httpx.Response(404, json={"error": f"unstubbed path {path}"})

    @property
    def token_requests(self) -> list[httpx.Request]:
        """Only the calls made to the token endpoint."""
        return [r for r in self.requests if r.url.host == "accounts.spotify.com"]


def _build_app(settings: Settings, handler: Handler) -> tuple[TestClient, Any]:
    """Create the app and swap its Spotify adapters for the stub transport."""
    app = create_app(settings)
    mock_http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    token_store = app.state.spotify_token_store
    app.state.spotify_auth_service = SpotifyAuthService(
        app.state.spotify_oauth, token_store, mock_http
    )
    app.state.spotify_client = SpotifyApiClient(mock_http)
    app.state.music_provider = SpotifyMusicProvider(app.state.spotify_client)
    app.state.http_client = mock_http
    return TestClient(app), app


@pytest.fixture
def spotify_stub() -> SpotifyStub:
    """A fresh stub with sensible defaults."""
    return SpotifyStub()


@pytest.fixture
def spotify_client(settings: Settings, spotify_stub: SpotifyStub) -> TestClient:
    """Test client whose outbound Spotify traffic is fully stubbed."""
    client, _ = _build_app(settings, spotify_stub)
    return client


@pytest.fixture
def linked_client(settings: Settings, spotify_stub: SpotifyStub) -> TestClient:
    """Client already holding a signed session cookie bound to stored tokens."""
    client, app = _build_app(settings, spotify_stub)
    seed_token(app, "session-linked")
    client.cookies.set(SESSION_COOKIE, sign("session-linked", "test-session-secret"))
    return client


def seed_token(app: Any, session_id: str, *, expires_in: float = 3600.0) -> None:
    """Put a token bundle into the application's store for ``session_id``.

    The store is async-only, but seeding is a test-time side effect, so the
    in-memory dict is written directly instead of spinning up an event loop.
    """
    bundle = TokenBundle(
        access_token="access-token-1",
        refresh_token="refresh-token-1",
        expires_at=time.time() + expires_in,
        scope="streaming",
    )
    app.state.spotify_token_store._store[session_id] = bundle


@pytest.fixture
def create_playlist(client: TestClient) -> Callable[..., PlaylistPayload]:
    """Create a playlist over HTTP and return its payload."""

    def _create(name: str = "Queue") -> PlaylistPayload:
        response = client.post("/api/playlists", json={"name": name})
        assert response.status_code == 201, response.text
        return response.json()

    return _create


@pytest.fixture
def filled_playlist(client: TestClient) -> Callable[..., PlaylistPayload]:
    """Create a playlist already filled with ``count`` local songs."""

    def _build(*, name: str = "Queue", count: int = 3, duration: float = 180.0) -> PlaylistPayload:
        created = client.post("/api/playlists", json={"name": name})
        assert created.status_code == 201, created.text
        playlist_id = created.json()["id"]
        for index in range(count):
            response = client.post(
                f"/api/playlists/{playlist_id}/songs",
                json={
                    "song": {
                        "id": f"local-{index}",
                        "title": f"Song {index}",
                        "artist": "MigMusic",
                        "source": "local",
                        "duration": duration,
                    }
                },
            )
            assert response.status_code == 201, response.text
        return client.get(f"/api/playlists/{playlist_id}").json()

    return _build
