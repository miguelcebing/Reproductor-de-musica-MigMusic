"""Where a song is played from.

The list itself only knows the *source* of a song; switching between the local
HTML5 player and the Spotify SDK is a frontend concern (Strategy pattern).
"""

from __future__ import annotations

from enum import StrEnum


class AudioSourceType(StrEnum):
    """Two independent, polymorphic sources (never mixed inside one player)."""

    LOCAL = "local"
    SPOTIFY = "spotify"
