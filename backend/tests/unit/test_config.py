"""Tests for ``migmusic.core.config``."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from migmusic.core import Settings, clear_settings_cache, get_settings


def test_settings_load_from_environment(settings: Settings) -> None:
    """Required values are read from the environment with the declared names."""
    assert settings.app_env == "development"
    assert settings.spotify_client_id == "test-client-id"
    assert settings.spotify_redirect_uri == "http://127.0.0.1:5173/callback"


def test_missing_required_variable_fails_fast(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A missing secret must prevent the application from starting."""
    monkeypatch.delenv("SPOTIFY_CLIENT_SECRET", raising=False)
    clear_settings_cache()

    with pytest.raises(ValidationError) as excinfo:
        Settings(_env_file=None)

    assert "SPOTIFY_CLIENT_SECRET" in str(excinfo.value)


def test_trailing_slash_is_stripped_from_redirect_uri(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Spotify matches redirect URIs exactly, so a trailing slash must not survive."""
    monkeypatch.setenv("SPOTIFY_REDIRECT_URI", "https://migmusic.vercel.app/callback/")
    clear_settings_cache()

    settings = Settings(_env_file=None)

    assert settings.spotify_redirect_uri == "https://migmusic.vercel.app/callback"


def test_cors_origins_always_include_frontend_origin(settings: Settings) -> None:
    """The declared frontend origin is never missing from the CORS allow-list."""
    assert settings.frontend_origin in settings.cors_origins
    assert len(settings.cors_origins) == len(set(settings.cors_origins))


def test_repr_does_not_leak_secrets(settings: Settings) -> None:
    """Debug output must never contain credential values."""
    rendered = repr(settings)

    assert "test-client-secret" not in rendered
    assert "test-session-secret" not in rendered
    assert "***" in rendered


def test_is_production_flag(settings: Settings) -> None:
    """The production flag mirrors ``APP_ENV``."""
    assert settings.is_production is False


def test_get_settings_returns_the_cached_instance() -> None:
    """The process-wide accessor is built once and then reused."""
    clear_settings_cache()

    first = get_settings()

    assert get_settings() is first
    assert first.app_env == "development"
    assert first.skip_seconds == 5.0
