"""Property-based tests (``TEST-004``): the list must match a reference model.

The model here is a plain Python ``list`` — allowed in tests, forbidden as
storage in production code. Hypothesis builds random operation sequences and
the test asserts, after every single step, that

* the payload order is identical to the model,
* every invariant still holds,
* the cursor follows the documented rules (``PLAYLIST-009a/b``),
* invalid operations are rejected in both worlds alike.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from migmusic.domain import (
    DoublyLinkedList,
    EmptyPlaylistError,
    InvalidPositionError,
    ItemNotFoundError,
)

Op = tuple[object, ...]

# Each branch produces one operation as a tuple: (kind, ...arguments).
operations = st.one_of(
    st.tuples(st.just("begin"), st.integers(min_value=-3, max_value=3)),
    st.tuples(st.just("end"), st.integers(min_value=-3, max_value=3)),
    st.tuples(
        st.just("at"),
        st.integers(min_value=-3, max_value=8),
        st.integers(min_value=-3, max_value=3),
    ),
    st.tuples(st.just("remove_at"), st.integers(min_value=-3, max_value=8)),
    st.tuples(st.just("move_to"), st.integers(min_value=-3, max_value=8)),
    st.tuples(st.just("find"), st.integers(min_value=-3, max_value=3)),
    st.tuples(st.just("remove_value"), st.integers(min_value=-3, max_value=3)),
    st.tuples(st.just("next")),
    st.tuples(st.just("previous")),
    st.tuples(st.just("clear")),
)


class Model:
    """Reference implementation: a plain list plus a cursor index."""

    def __init__(self) -> None:
        self.items: list[int] = []
        self.cursor: int | None = None

    @property
    def current(self) -> int | None:
        """Song under the cursor, mirroring ``DoublyLinkedList.get_current``."""
        if self.cursor is None:
            return None
        return self.items[self.cursor]


def _expect_invalid(action: Callable[[], object]) -> None:
    """An out-of-range position or an empty list must be rejected."""
    with pytest.raises((InvalidPositionError, EmptyPlaylistError)):
        action()


def _sync_after_removal(model: Model, removed: int) -> None:
    """PLAYLIST-009b: next song, or the previous one when the tail was removed."""
    if model.cursor is None:
        return
    if model.cursor == removed:
        if not model.items:
            model.cursor = None
        else:
            model.cursor = removed if removed < len(model.items) else removed - 1
    elif model.cursor > removed:
        model.cursor -= 1


def _apply(model: Model, linked: DoublyLinkedList[int], op: Op) -> None:
    """Apply one operation to both implementations, then compare the result."""
    kind = op[0]

    if kind == "begin":
        value = int(op[1])
        model.items.insert(0, value)
        linked.insert_at_beginning(value)
        if model.cursor is None:
            model.cursor = 0
        else:  # the current node shifted one position to the right
            model.cursor += 1

    elif kind == "end":
        value = int(op[1])
        model.items.append(value)
        linked.insert_at_end(value)
        if model.cursor is None:
            model.cursor = 0

    elif kind == "at":
        position, value = int(op[1]), int(op[2])
        if position < 0 or position > len(model.items):
            _expect_invalid(lambda: linked.insert_at(position, value))
            return
        was_empty = model.cursor is None
        model.items.insert(position, value)
        linked.insert_at(position, value)
        if was_empty:
            model.cursor = 0  # the list points the cursor at the only node
        elif position <= model.cursor:
            model.cursor += 1  # the current node shifted to the right

    elif kind == "remove_at":
        position = int(op[1])
        if position < 0 or position >= len(model.items):
            _expect_invalid(lambda: linked.remove_at(position))
            return
        del model.items[position]
        linked.remove_at(position)
        _sync_after_removal(model, position)

    elif kind == "move_to":
        position = int(op[1])
        if position < 0 or position >= len(model.items):
            _expect_invalid(lambda: linked.move_to(position))
            return
        model.cursor = position
        assert linked.move_to(position) == model.items[position]

    elif kind == "next":
        moved = linked.move_next()
        if model.cursor is None or model.cursor == len(model.items) - 1:
            assert moved is False  # PLAYLIST-009a: stop at the tail
        else:
            assert moved is True
            model.cursor += 1

    elif kind == "previous":
        moved = linked.move_previous()
        if model.cursor is None or model.cursor == 0:
            assert moved is False  # PLAYLIST-009a: stop at the head
        else:
            assert moved is True
            model.cursor -= 1

    elif kind == "find":
        value = int(op[1])
        expected = model.items.index(value) if value in model.items else None
        assert linked.find(value) == expected

    elif kind == "remove_value":
        value = int(op[1])
        if value not in model.items:
            with pytest.raises(ItemNotFoundError):
                linked.remove(value)
            return
        position = model.items.index(value)
        del model.items[position]
        linked.remove(value)
        _sync_after_removal(model, position)

    elif kind == "clear":
        model.items.clear()
        model.cursor = None
        linked.clear()

    assert linked.to_list() == model.items
    assert len(linked) == len(model.items)
    assert linked.get_current() == model.current
    linked.assert_invariants()


@given(st.lists(operations, max_size=30))
@settings(deadline=None, max_examples=300)
def test_random_operations_match_a_reference_list(ops: list[Op]) -> None:
    """Any operation sequence leaves the list identical to a plain Python list."""
    model = Model()
    linked: DoublyLinkedList[int] = DoublyLinkedList()

    for op in ops:
        _apply(model, linked, op)


@given(st.integers(min_value=0, max_value=20))
@settings(deadline=None, max_examples=100)
def test_build_up_and_tear_down_returns_to_the_empty_invariants(size: int) -> None:
    """Filling and emptying the list restores all four 'empty' fields."""
    linked: DoublyLinkedList[int] = DoublyLinkedList()
    for value in range(size):
        linked.insert_at_end(value)
    linked.assert_invariants()

    while linked.size:
        linked.remove_at(linked.size - 1)
    linked.assert_invariants()

    assert linked.head is None
    assert linked.tail is None
    assert linked.current is None
    assert linked.to_list() == []


@given(st.lists(st.integers(min_value=0, max_value=99), max_size=40, unique=True))
@settings(deadline=None, max_examples=100)
def test_forward_walk_matches_to_list(values: list[int]) -> None:
    """Traversing with ``move_next`` visits exactly the same songs, in order."""
    linked: DoublyLinkedList[int] = DoublyLinkedList()
    for value in values:
        linked.insert_at_end(value)
    linked.assert_invariants()

    visited: list[int] = []
    first = linked.get_current()
    if first is not None:
        visited.append(first)
        while linked.move_next():
            current = linked.get_current()
            assert current is not None
            visited.append(current)

    assert visited == values
