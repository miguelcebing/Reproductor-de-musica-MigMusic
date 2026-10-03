"""Tests for the in-memory TTL cache."""

from __future__ import annotations

import time

import pytest

from migmusic.infrastructure.cache import TtlCache


def test_get_returns_a_stored_value() -> None:
    cache: TtlCache[str, int] = TtlCache(ttl=60)

    cache.set("a", 1)

    assert cache.get("a") == 1
    assert cache.get("missing") is None


def test_entries_expire_after_the_ttl() -> None:
    cache: TtlCache[str, int] = TtlCache(ttl=0.02)
    cache.set("a", 1)

    time.sleep(0.1)
    assert cache.get("a") is None


def test_evicts_the_oldest_entry_when_full() -> None:
    cache: TtlCache[str, int] = TtlCache(ttl=60, max_size=2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)

    assert len([key for key in ("a", "b", "c") if cache.get(key) is not None]) == 2


@pytest.mark.parametrize("ttl", [0, -1])
def test_rejects_a_non_positive_ttl(ttl: float) -> None:
    with pytest.raises(ValueError, match="ttl"):
        TtlCache(ttl=ttl)


def test_clear_drops_everything() -> None:
    cache: TtlCache[str, int] = TtlCache(ttl=60)
    cache.set("a", 1)

    cache.clear()

    assert cache.get("a") is None
