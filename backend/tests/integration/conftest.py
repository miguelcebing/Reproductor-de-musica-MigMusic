"""Fixtures shared by the HTTP-level tests.

Each test gets a fresh application (and therefore a fresh repository), so no
state leaks between cases.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

PlaylistPayload = dict[str, Any]


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
