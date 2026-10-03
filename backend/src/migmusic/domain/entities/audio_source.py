"""Where a song is played from.

The list itself only knows the *source* of a song; switching between the local
HTML5 player and the Spotify SDK is a frontend concern (Strategy pattern).
"""

from __future__ import annotations

from enum import StrEnum


class AudioSourceType(StrEnum):
    """Independent, polymorphic sources (never mixed inside one player).

    ``YOUTUBE`` tracks carry a ``videoId`` and are played by the official
    YouTube IFrame player in the browser; the backend only serves metadata.
    """

    LOCAL = "local"
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
