"""Shared pytest fixtures.

The environment is seeded at module import time, *before* any ``migmusic``
module is imported, so ``Settings`` can be built without a real ``.env`` file
or real Spotify credentials.
"""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

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
from migmusic.core import Settings, clear_settings_cache  # noqa: E402
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


@pytest.fixture
def client(settings: Settings) -> Iterator[TestClient]:
    """ASGI test client against a freshly built application."""
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client
