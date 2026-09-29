"""Tests for the smallest unit of the structure: the node itself."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from migmusic.domain import Node, Song


def test_node_defaults_to_no_neighbours(make_song: Callable[..., Song]) -> None:
    """A brand new node points at nothing in either direction."""
    node = Node(song=make_song())

    assert node.previous is None
    assert node.next is None


def test_node_links_are_mutable(make_song: Callable[..., Song]) -> None:
    """Nodes are plain mutable containers; the list owns the linking rules."""
    first = Node(song=make_song())
    second = Node(song=make_song())

    first.next = second
    second.previous = first

    assert first.next is second
    assert second.previous is first


def test_node_is_generic_over_its_payload() -> None:
    """The structure is reusable: payloads are not hard-coded to Song."""
    node: Node[int] = Node(song=7)

    assert node.song == 7
    with pytest.raises(AttributeError):
        node.value = 1  # type: ignore[attr-defined]
