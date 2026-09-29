"""Thin HTTP controllers: no business logic lives here."""

from migmusic.api.routers import health, playback, playlists

__all__ = ["health", "playback", "playlists"]
