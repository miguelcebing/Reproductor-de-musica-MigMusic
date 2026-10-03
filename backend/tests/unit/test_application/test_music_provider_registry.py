"""Tests for the source→provider registry."""

from __future__ import annotations

import pytest

from migmusic.application.services.music_provider_registry import MusicProviderRegistry
from migmusic.domain.entities.audio_source import AudioSourceType


def test_get_returns_the_registered_provider() -> None:
    sentinel = object()
    registry = MusicProviderRegistry({AudioSourceType.YOUTUBE: sentinel})  # type: ignore[dict-item]

    assert registry.get(AudioSourceType.YOUTUBE) is sentinel
    assert registry.has(AudioSourceType.YOUTUBE) is True


def test_get_raises_for_an_unregistered_source() -> None:
    registry = MusicProviderRegistry({})

    with pytest.raises(KeyError):
        registry.get(AudioSourceType.SPOTIFY)
    assert registry.has(AudioSourceType.SPOTIFY) is False


def test_local_is_not_a_backend_provider() -> None:
    """Local audio lives in the browser, so it is never registered here."""
    registry = MusicProviderRegistry({})

    assert registry.has(AudioSourceType.LOCAL) is False
