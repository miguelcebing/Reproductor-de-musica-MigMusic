"""Maps an :class:`AudioSourceType` to its :class:`MusicProvider`.

Adding a new remote source is "open for extension, closed for modification":
register one provider here (in the composition root) and no existing code
changes. Local audio is *not* registered: its bytes live in the browser, so it
is handled entirely by the frontend player, not by a backend catalog.
"""

from __future__ import annotations

from migmusic.domain.entities.audio_source import AudioSourceType
from migmusic.domain.ports.music_provider import MusicProvider


class MusicProviderRegistry:
    """Look up the catalog adapter for a source, or fail loudly."""

    def __init__(self, providers: dict[AudioSourceType, MusicProvider]) -> None:
        self._providers = dict(providers)

    def get(self, source: AudioSourceType) -> MusicProvider:
        """Return the provider for ``source``; raises ``KeyError`` when absent."""
        try:
            return self._providers[source]
        except KeyError as exc:
            raise KeyError(f"no music provider registered for {source!r}") from exc

    def has(self, source: AudioSourceType) -> bool:
        """Whether a provider is registered for ``source``."""
        return source in self._providers


__all__ = ["MusicProviderRegistry"]
