"""Shared pytest fixtures.

The environment is seeded at module import time, *before* any ``migmusic``
module is imported, so ``Settings`` can be built without a real ``.env`` file
or real Spotify credentials.
"""

from __future__ import annotations

import itertools
import os
import random
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

if TYPE_CHECKING:
    from migmusic.application.services import PlaybackService, PlaylistService
    from migmusic.domain import Playlist, Song
    from migmusic.infrastructure.persistence import InMemoryPlaylistRepository

# Dummy values: no real secret is ever loaded in the test suite.
_TEST_ENV = {
    "APP_ENV": "development",
    "LOG_LEVEL": "WARNING",
    "FRONTEND_ORIGIN": "http://127.0.0.1:5173",
    "ALLOWED_ORIGINS": "http://127.0.0.1:5173",
    "SPOTIFY_CLIENT_ID": "test-client-id",
    "SPOTIFY_CLIENT_SECRET": "test-client-secret",
    "SPOTIFY_REDIRECT_URI": "http://127.0.0.1:5173/callback",
    "SESSION_SECRET_KEY": "test-session-secret",
    "DATABASE_URL": "",
}

_previous_env = {key: os.environ.get(key) for key in _TEST_ENV}
os.environ.update(_TEST_ENV)

# Imported only after the environment is seeded.
from migmusic.application.services import (  # noqa: E402
    PlaybackService,
    PlaylistService,
)
from migmusic.core import Settings, clear_settings_cache  # noqa: E402
from migmusic.infrastructure.persistence import InMemoryPlaylistRepository  # noqa: E402
from migmusic.main import create_app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _restore_environment() -> Iterator[None]:
    """Undo the env override once the whole session has finished."""
    yield
    for key, value in _previous_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
    clear_settings_cache()


@pytest.fixture
def settings() -> Settings:
    """Settings built from the seeded test environment."""
    clear_settings_cache()
    return Settings(_env_file=None)


TEST_DEVICE_ID = "test-device"


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """ASGI test client whose default headers carry the required device id."""
    app = create_app(settings)
    with TestClient(app) as test_client:
        test_client.headers.update({"X-Device-Id": TEST_DEVICE_ID})
        yield test_client


@pytest.fixture
def repository() -> InMemoryPlaylistRepository:
    """Fresh repository per test, so cases never share state."""
    return InMemoryPlaylistRepository()


@pytest.fixture
def playlist_service(repository: InMemoryPlaylistRepository) -> PlaylistService:
    """Playlist use cases wired to the in-memory adapter."""
    return PlaylistService(repository)


@pytest.fixture
def playback_service(repository: InMemoryPlaylistRepository) -> PlaybackService:
    """Playback use cases with a seeded RNG so shuffle stays deterministic."""
    return PlaybackService(repository, rng=random.Random(0))


@pytest.fixture
def make_song() -> Callable[..., Song]:
    """Factory producing unique local :class:`Song` instances.

    Usage: ``song = make_song()`` or ``make_song(title="Nocturne")``.
    """
    from migmusic.domain import AudioSourceType, Song

    counter = itertools.count(1)

    def _make(**overrides: object) -> Song:
        index = next(counter)
        values: dict[str, object] = {
            "id": f"local-{index}",
            "title": f"Song {index}",
            "artist": "MigMusic",
            "source": AudioSourceType.LOCAL,
            "duration": 180.0,
        }
        values.update(overrides)
        return Song(**values)  # type: ignore[arg-type]

    return _make


@pytest.fixture
def seed_playlist(
    repository: InMemoryPlaylistRepository, make_song: Callable[..., Song]
) -> Callable[..., Playlist]:
    """Build and store a playlist with ``count`` local songs of ``duration`` seconds."""

    from migmusic.domain import Playlist

    def _seed(
        *, name: str = "Queue", count: int = 3, duration: float = 180.0, owner_id: str = "device-a"
    ) -> Playlist:
        playlist = Playlist(name)
        for _ in range(count):
            playlist.add(make_song(duration=duration))
        repository.save(playlist, owner_id=owner_id)
        return playlist

    return _seed
