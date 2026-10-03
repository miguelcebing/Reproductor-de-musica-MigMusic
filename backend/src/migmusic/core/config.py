"""Application settings.

Reads configuration from environment variables (optionally from a local `.env`)
and fails fast when a required variable is missing. Secrets are never logged and
never reach the frontend.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

EnvironmentName = Literal["development", "staging", "production"]


@dataclass(frozen=True, slots=True)
class SpotifyConfig:
    """Spotify OAuth configuration extracted from Settings."""

    client_id: str
    client_secret: str
    redirect_uri: str
    scopes: str


class Settings(BaseSettings):
    """Typed application configuration.

    Required variables raise a validation error at import time, so a misconfigured
    deployment never starts serving traffic.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application ---
    app_env: EnvironmentName = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # --- HTTP / CORS ---
    frontend_origin: str = Field(default="http://127.0.0.1:5173", alias="FRONTEND_ORIGIN")
    allowed_origins: str = Field(default="", alias="ALLOWED_ORIGINS")

    # --- Spotify (secrets stay server-side) ---
    spotify_client_id: str = Field(alias="SPOTIFY_CLIENT_ID")
    spotify_client_secret: SecretStr = Field(alias="SPOTIFY_CLIENT_SECRET")
    spotify_redirect_uri: str = Field(alias="SPOTIFY_REDIRECT_URI")
    spotify_scopes: str = Field(
        default="streaming user-read-email user-read-private "
        "user-read-playback-state user-modify-playback-state "
        "playlist-read-private user-library-read user-follow-read",
        alias="SPOTIFY_SCOPES",
    )

    # --- Session ---
    session_secret_key: SecretStr = Field(alias="SESSION_SECRET_KEY")
    # How long a Spotify login may stay unfinished (2FA + consent screen).
    oauth_state_max_age: int = Field(default=900, alias="OAUTH_STATE_MAX_AGE", ge=60)

    # --- Playback ---
    skip_seconds: float = Field(default=5.0, alias="SKIP_SECONDS", gt=0)

    # --- YouTube Music (unofficial, no auth: see ytmusicapi) ---
    youtube_music_enabled: bool = Field(default=True, alias="YOUTUBE_MUSIC_ENABLED")
    youtube_music_language: str = Field(default="en", alias="YOUTUBE_MUSIC_LANGUAGE")
    youtube_music_timeout_seconds: float = Field(
        default=8.0, alias="YOUTUBE_MUSIC_TIMEOUT_SECONDS", gt=0
    )

    # --- Persistence ---
    database_url: str = Field(default="", alias="DATABASE_URL")

    # --- Proxy ---
    render_backend_url: str = Field(default="", alias="RENDER_BACKEND_URL")

    # --- Derived ---

    @property
    def is_production(self) -> bool:
        """Whether the app is running in the production environment."""
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        """Explicit CORS origins, always including the frontend origin."""
        origins = {origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()}
        origins.add(self.frontend_origin)
        return sorted(origins)

    @field_validator("spotify_redirect_uri")
    @classmethod
    def _redirect_uri_must_not_have_trailing_slash(cls, value: str) -> str:
        """Spotify matches redirect URIs exactly, so a trailing slash breaks login."""
        return value.rstrip("/")

    @property
    def spotify(self) -> SpotifyConfig:
        """Extract Spotify config for the OAuth module."""
        return SpotifyConfig(
            client_id=self.spotify_client_id,
            client_secret=self.spotify_client_secret.get_secret_value(),
            redirect_uri=self.spotify_redirect_uri,
            scopes=self.spotify_scopes,
        )

    def __repr__(self) -> str:
        """Render settings without exposing secrets."""
        return (
            f"Settings(app_env={self.app_env!r}, log_level={self.log_level!r}, "
            f"frontend_origin={self.frontend_origin!r}, cors_origins={self.cors_origins!r}, "
            f"spotify_client_id={'***' if self.spotify_client_id else ''}, "
            f"spotify_client_secret=***, session_secret_key=***, "
            f"database_url={'***' if self.database_url else ''})"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings instance (cached)."""
    return Settings()


def clear_settings_cache() -> None:
    """Drop the cached settings (used by tests)."""
    get_settings.cache_clear()
