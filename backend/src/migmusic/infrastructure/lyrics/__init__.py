"""Lyrics infrastructure adapters."""

from migmusic.infrastructure.lyrics.errors import LrclibError
from migmusic.infrastructure.lyrics.lrclib_client import LrclibClient

__all__ = ["LrclibClient", "LrclibError"]
