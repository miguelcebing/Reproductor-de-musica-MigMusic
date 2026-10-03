"""YouTube Music adapter (unofficial ``ytmusicapi``, keyless).

Kept behind :class:`~migmusic.domain.ports.music_provider.MusicProvider` so the
rest of the system never touches the library directly.
"""

from migmusic.infrastructure.youtube.youtube_music_provider import YouTubeMusicProvider
from migmusic.infrastructure.youtube.ytmusic_client import YtMusicClient

__all__ = ["YouTubeMusicProvider", "YtMusicClient"]
