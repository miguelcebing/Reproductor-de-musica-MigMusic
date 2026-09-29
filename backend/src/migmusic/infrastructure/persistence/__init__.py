"""Persistence adapters implementing the domain ports."""

from migmusic.infrastructure.persistence.in_memory_playlist_repository import (
    InMemoryPlaylistRepository,
)

__all__ = ["InMemoryPlaylistRepository"]
