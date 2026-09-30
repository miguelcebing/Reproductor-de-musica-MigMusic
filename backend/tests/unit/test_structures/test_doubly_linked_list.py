"""Exhaustive behavioural tests for the doubly linked list (SKILL2).

Every operation is covered for: empty / one / two / many elements, head, tail,
middle, invalid positions, removing the cursor, and both edge policies.
Invariants 1-5 are re-checked after every mutation through ``assert_invariants``.
"""

from __future__ import annotations

from collections.abc import Callable

import pytest

from migmusic.domain import (
    AudioSourceType,
    DoublyLinkedList,
    EmptyPlaylistError,
    InvalidPositionError,
    ItemNotFoundError,
    Song,
)

# --------------------------------------------------------------------- setup


def _song(title: str) -> Song:
    """Deterministic song, usable where fixtures are not available."""
    return Song(
        id=f"local-{title}",
        title=title,
        artist="MigMusic",
        source=AudioSourceType.LOCAL,
    )


@pytest.fixture
def empty() -> DoublyLinkedList[Song]:
    """An empty list, cursor and all."""
    return DoublyLinkedList[Song]()


@pytest.fixture
def three() -> DoublyLinkedList[Song]:
    """``head -> A <-> B <-> C <- tail`` with the cursor on ``A``.

    Built with the deterministic ``_song`` helper so every assertion can
    compare songs by value (ids included).
    """
    linked = DoublyLinkedList[Song]()
    for title in "ABC":
        linked.insert_at_end(_song(title))
    linked.assert_invariants()
    return linked


def titles(linked: DoublyLinkedList[Song]) -> list[str]:
    """Titles in traversal order (the model used to compare against)."""
    return [song.title for song in linked]


def check(linked: DoublyLinkedList[Song]) -> None:
    """Every invariant, after every operation."""
    linked.assert_invariants()


# ----------------------------------------------------------------- emptiness


def test_empty_list_has_no_nodes(empty: DoublyLinkedList[Song]) -> None:
    """Invariant 1: all four fields agree that the list is empty."""
    assert empty.is_empty()
    assert empty.size == 0
    assert empty.get_size() == 0
    assert len(empty) == 0
    assert empty.head is None
    assert empty.tail is None
    assert empty.current is None
    assert empty.get_current() is None
    check(empty)


def test_empty_list_refuses_to_walk(empty: DoublyLinkedList[Song]) -> None:
    """Moving on an empty list is a no-op, not an error."""
    assert empty.move_next() is False
    assert empty.move_previous() is False
    check(empty)


def test_empty_list_refuses_selection_and_removal(empty: DoublyLinkedList[Song]) -> None:
    """``move_to``/``remove_at`` need at least one song (``EmptyPlaylistError``)."""
    with pytest.raises(EmptyPlaylistError):
        empty.move_to(0)
    with pytest.raises(EmptyPlaylistError):
        empty.remove_at(0)
    check(empty)


def test_empty_list_serialises_and_clears(empty: DoublyLinkedList[Song]) -> None:
    """Snapshots and ``clear`` are safe on an empty list."""
    assert empty.to_list() == []
    assert list(empty.iter_nodes()) == []
    assert not any(empty)

    empty.clear()
    check(empty)


# ------------------------------------------------------------------- insert


def test_insert_at_beginning_makes_the_only_node_everything(
    empty: DoublyLinkedList[Song], make_song: Callable[..., Song]
) -> None:
    """With one node, head, tail and current all point at it."""
    song = make_song(title="Solo")
    node = empty.insert_at_beginning(song)

    assert empty.head is node
    assert empty.tail is node
    assert empty.current is node
    assert empty.get_current() is song
    assert titles(empty) == ["Solo"]
    check(empty)


def test_insert_at_beginning_keeps_head_and_previous_null(
    empty: DoublyLinkedList[Song], make_song: Callable[..., Song]
) -> None:
    """Inserting at the front re-links head and keeps ``head.previous`` null."""
    first = make_song(title="First")
    second = make_song(title="Second")

    empty.insert_at_beginning(first)
    node = empty.insert_at_beginning(second)

    assert empty.head is node
    assert node.previous is None
    assert node.next is not None
    assert node.next.song is first
    assert empty.tail is not None and empty.tail.song is first
    assert titles(empty) == ["Second", "First"]
    check(empty)


def test_insert_at_end_appends_and_keeps_tail_next_null(
    empty: DoublyLinkedList[Song], make_song: Callable[..., Song]
) -> None:
    """Appending keeps ``tail.next`` null and leaves the cursor alone."""
    first = make_song(title="First")
    second = make_song(title="Second")

    node = empty.insert_at_end(first)
    assert empty.current is node

    empty.insert_at_end(second)
    assert empty.current is node  # the cursor never jumps on insert
    assert empty.tail is not None and empty.tail.song is second
    assert empty.tail.next is None
    assert titles(empty) == ["First", "Second"]
    check(empty)


@pytest.mark.parametrize("position", [0, 1, 2, 3])
def test_insert_at_covers_every_position(three: DoublyLinkedList[Song], position: int) -> None:
    """``insert_at`` accepts the whole ``0 .. size`` range."""
    expected = ["A", "B", "C"]
    expected.insert(position, "X")

    three.insert_at(position, _song("X"))
    assert titles(three) == expected
    check(three)


def test_insert_at_middle_links_both_directions(three: DoublyLinkedList[Song]) -> None:
    """The classic four-step insert never loses a reference."""
    three.insert_at(1, _song("X"))

    assert [node.song.title for node in three.iter_nodes()] == ["A", "X", "B", "C"]
    middle = three.head.next  # type: ignore[union-attr]
    assert middle is not None
    assert middle.previous is not None and middle.previous.song.title == "A"
    assert middle.next is not None and middle.next.song.title == "B"
    assert middle.next.previous is middle
    check(three)


@pytest.mark.parametrize("position", [-1, 4, 99])
def test_insert_at_rejects_positions_outside_the_range(
    three: DoublyLinkedList[Song], position: int
) -> None:
    """Negative or too-large positions raise ``InvalidPositionError``."""
    with pytest.raises(InvalidPositionError):
        three.insert_at(position, _song("X"))
    assert titles(three) == ["A", "B", "C"]
    check(three)


# ------------------------------------------------------------------- remove


def test_remove_by_value_returns_the_song(three: DoublyLinkedList[Song]) -> None:
    """Removing by value searches the chain and repairs both neighbours."""
    removed = three.remove(_song("B"))

    assert removed.title == "B"
    assert titles(three) == ["A", "C"]
    check(three)


def test_remove_by_node_is_supported(three: DoublyLinkedList[Song]) -> None:
    """Passing a node avoids the O(n) search (O(1) removal)."""
    node = three.head.next
    assert node is not None

    removed = three.remove(node)

    assert removed.title == "B"
    assert titles(three) == ["A", "C"]
    check(three)


def test_remove_unknown_song_raises(three: DoublyLinkedList[Song]) -> None:
    """A value that is not in the list cannot be removed."""
    with pytest.raises(ItemNotFoundError):
        three.remove(_song("Z"))
    check(three)


def test_remove_head_updates_head(three: DoublyLinkedList[Song]) -> None:
    """Removing the head promotes the next node and clears its ``previous``."""
    three.remove(_song("A"))

    assert three.head is not None and three.head.song.title == "B"
    assert three.head.previous is None
    check(three)


def test_remove_tail_updates_tail(three: DoublyLinkedList[Song]) -> None:
    """Removing the tail promotes the previous node and clears its ``next``."""
    three.remove(_song("C"))

    assert three.tail is not None and three.tail.song.title == "B"
    assert three.tail.next is None
    check(three)


def test_remove_current_head_moves_cursor_forward(three: DoublyLinkedList[Song]) -> None:
    """PLAYLIST-009b: removing the cursor advances it to the next song."""
    assert three.current is not None and three.current.song.title == "A"

    three.remove(_song("A"))

    assert three.current is not None and three.current.song.title == "B"
    check(three)


def test_remove_current_tail_moves_cursor_backwards(three: DoublyLinkedList[Song]) -> None:
    """PLAYLIST-009b: at the tail there is no 'next', so the cursor goes back."""
    three.move_to(2)
    assert three.current is not None and three.current.song.title == "C"

    three.remove_at(2)

    assert three.current is not None and three.current.song.title == "B"
    check(three)


def test_remove_current_middle_moves_cursor_forward(three: DoublyLinkedList[Song]) -> None:
    """PLAYLIST-009b: a middle removal keeps playback on the following song."""
    three.move_to(1)

    three.remove_at(1)

    assert three.current is not None and three.current.song.title == "C"
    check(three)


def test_removing_the_only_node_empties_the_list(make_song: Callable[..., Song]) -> None:
    """PLAYLIST-009b: with no neighbour left the cursor becomes ``None``."""
    linked = DoublyLinkedList[Song]()
    linked.insert_at_end(make_song())
    linked.assert_invariants()

    linked.remove_at(0)

    assert linked.size == 0
    assert linked.current is None
    linked.assert_invariants()


def test_remove_at_returns_the_removed_song(three: DoublyLinkedList[Song]) -> None:
    """``remove_at`` reports which song left the playlist."""
    removed = three.remove_at(1)

    assert removed.title == "B"
    assert titles(three) == ["A", "C"]
    check(three)


@pytest.mark.parametrize("position", [-1, 3, 10])
def test_remove_at_rejects_positions_outside_the_range(
    three: DoublyLinkedList[Song], position: int
) -> None:
    """Only ``0 .. size - 1`` can be removed."""
    with pytest.raises(InvalidPositionError):
        three.remove_at(position)
    check(three)


def test_remove_first_occurrence_allows_duplicates(
    empty: DoublyLinkedList[Song], make_song: Callable[..., Song]
) -> None:
    """Duplicates are permitted; ``remove`` takes the first match."""
    empty.insert_at_end(make_song(title="Same"))
    empty.insert_at_end(make_song(title="Same"))

    empty.remove_at(0)

    assert titles(empty) == ["Same"]
    check(empty)


# --------------------------------------------------------------------- find


def test_find_returns_the_index(three: DoublyLinkedList[Song]) -> None:
    """Search by value returns the position the UI needs to highlight."""
    assert three.find(_song("B")) == 1
    assert three.find(_song("A")) == 0
    assert three.find(_song("C")) == 2
    check(three)


def test_find_returns_none_for_unknown_values(three: DoublyLinkedList[Song]) -> None:
    """A miss is reported as ``None``, not as an exception."""
    assert three.find(_song("Z")) is None


def test_find_by_uses_a_predicate(three: DoublyLinkedList[Song]) -> None:
    """Predicate search backs the in-playlist search feature (``FEAT-001-c``)."""
    assert three.find_by(lambda song: song.title.startswith("B")) == 1
    assert three.find_by(lambda song: song.title.startswith("Z")) is None


def test_membership_operator(three: DoublyLinkedList[Song]) -> None:
    """``in`` mirrors ``find`` for the UI's 'is it already queued?' check."""
    assert _song("B") in three
    assert _song("Z") not in three


def test_get_at_reads_without_moving_the_cursor(three: DoublyLinkedList[Song]) -> None:
    """Index reads are side-effect free (searching must never select)."""
    three.move_to(2)

    assert three.get_at(1).title == "B"
    assert three.current_index == 2


def test_replace_at_swaps_the_payload_and_keeps_the_node(
    three: DoublyLinkedList[Song],
) -> None:
    """Favourites flip a value in place: links, order and cursor all survive."""
    three.move_to(1)
    replacement = _song("B2")

    previous = three.replace_at(1, replacement)

    assert previous.title == "B"
    assert titles(three) == ["A", "B2", "C"]
    assert three.current_index == 1
    assert three.current is not None and three.current.song is replacement
    check(three)


def test_get_at_and_replace_at_reject_positions_outside_the_range(
    three: DoublyLinkedList[Song],
) -> None:
    """Bounds behave like ``remove_at``: 422 through the error mapping."""
    with pytest.raises(InvalidPositionError):
        three.get_at(99)
    with pytest.raises(InvalidPositionError):
        three.replace_at(-1, _song("X"))


def test_get_at_and_replace_at_refuse_an_empty_list(empty: DoublyLinkedList[Song]) -> None:
    """An empty list has nothing to read or replace."""
    with pytest.raises(EmptyPlaylistError):
        empty.get_at(0)
    with pytest.raises(EmptyPlaylistError):
        empty.replace_at(0, _song("X"))


# ------------------------------------------------------------------ movement


def test_move_next_walks_forward_and_stops_at_the_tail(
    three: DoublyLinkedList[Song],
) -> None:
    """PLAYLIST-009 = A: the tail is a hard stop and ``current`` does not move."""
    assert three.move_next() is True
    assert three.current is not None and three.current.song.title == "B"

    assert three.move_next() is True
    assert three.current is not None and three.current.song.title == "C"

    assert three.move_next() is False  # tail: stop, do not wrap
    assert three.current is not None and three.current.song.title == "C"
    check(three)


def test_move_previous_walks_backwards_and_stops_at_the_head(
    three: DoublyLinkedList[Song],
) -> None:
    """PLAYLIST-009 = A: the head is a hard stop too."""
    three.move_to(2)

    assert three.move_previous() is True
    assert three.current is not None and three.current.song.title == "B"

    assert three.move_previous() is True
    assert three.current is not None and three.current.song.title == "A"

    assert three.move_previous() is False
    assert three.current is not None and three.current.song.title == "A"
    check(three)


def test_move_to_selects_a_song(three: DoublyLinkedList[Song]) -> None:
    """Selecting a row from the UI moves the cursor in O(n)."""
    selected = three.move_to(2)

    assert selected.title == "C"
    assert three.current is three.tail
    check(three)


@pytest.mark.parametrize("position", [-1, 3])
def test_move_to_rejects_positions_outside_the_range(
    three: DoublyLinkedList[Song], position: int
) -> None:
    """Selection must land on an existing song."""
    with pytest.raises(InvalidPositionError):
        three.move_to(position)
    check(three)


def test_double_direction_walks_use_the_closer_end() -> None:
    """Positions past the midpoint traverse from the tail (the point of DLL)."""
    linked: DoublyLinkedList[Song] = DoublyLinkedList()
    for index in range(10):
        linked.insert_at_end(_song(f"S{index}"))
    linked.assert_invariants()

    linked.move_to(8)  # > size / 2 -> walk backwards from tail
    assert linked.current is not None and linked.current.song.title == "S8"

    linked.remove_at(7)
    assert titles(linked) == [f"S{index}" for index in range(10) if index != 7]
    linked.assert_invariants()


# --------------------------------------------------------------------- clear


def test_clear_unlinks_every_node(three: DoublyLinkedList[Song]) -> None:
    """``clear`` resets all four fields and detaches the nodes."""
    first = three.head
    assert first is not None

    three.clear()

    assert three.size == 0
    assert three.head is None and three.tail is None and three.current is None
    assert first.next is None and first.previous is None
    check(three)


def test_list_is_reusable_after_clear(make_song: Callable[..., Song]) -> None:
    """Clearing is not terminal: the same object can be filled again."""
    linked = DoublyLinkedList[Song]()
    linked.insert_at_end(make_song())
    linked.clear()

    linked.insert_at_beginning(make_song(title="Fresh"))
    linked.insert_at_end(make_song(title="Next"))

    assert titles(linked) == ["Fresh", "Next"]
    check(linked)


def test_repr_reports_the_size(three: DoublyLinkedList[Song]) -> None:
    """Debug-friendly summary that never dumps every song."""
    assert repr(three) == "DoublyLinkedList(size=3)"


# ------------------------------------------------------------------ helpers
