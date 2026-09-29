"""Doubly linked list — the academic core of MigMusic.

Storage is made of real nodes only: no ``list``/``array`` is kept as an
alternative representation. ``to_list()`` exists purely to serialise or to feed
the didactic view (``UX-002``).

Edge policy (``PLAYLIST-009 = A``, ``PLAYLIST-009a``): reaching ``tail`` or
``head`` **stops** — ``move_next()``/``move_previous()`` return ``False`` and
leave ``current`` untouched. The list never wraps around; repeat modes are a
service-layer concern (``FEAT-001-d``).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Generic, TypeVar

from migmusic.domain.exceptions import (
    EmptyPlaylistError,
    InvalidPositionError,
    ItemNotFoundError,
)
from migmusic.domain.structures.node import Node

T = TypeVar("T")


class DoublyLinkedList(Generic[T]):
    """A doubly linked list with an explicit cursor (``current``).

    Invariants (verified by :meth:`assert_invariants`):

    1. ``size == 0`` iff ``head is None`` iff ``tail is None`` iff ``current is None``.
    2. ``head.previous is None`` and ``tail.next is None``.
    3. For every node ``n`` with ``n.next``, ``n.next.previous is n``.
    4. Walking forward from ``head`` visits exactly ``size`` nodes and ends at ``tail``.
    5. ``current``, when not ``None``, belongs to the list.
    """

    __slots__ = ("_current", "_head", "_size", "_tail")

    def __init__(self) -> None:
        """Create an empty list (O(1))."""
        self._head: Node[T] | None = None
        self._tail: Node[T] | None = None
        self._current: Node[T] | None = None
        self._size = 0

    # ------------------------------------------------------------------ read

    @property
    def head(self) -> Node[T] | None:
        """First node, or ``None`` when empty (read-only)."""
        return self._head

    @property
    def tail(self) -> Node[T] | None:
        """Last node, or ``None`` when empty (read-only)."""
        return self._tail

    @property
    def current(self) -> Node[T] | None:
        """Node the cursor points at, or ``None`` when empty (read-only)."""
        return self._current

    @property
    def size(self) -> int:
        """Number of nodes (read-only)."""
        return self._size

    def get_size(self) -> int:
        """Number of nodes — O(1) (``getSize()`` in the specification)."""
        return self._size

    def is_empty(self) -> bool:
        """``True`` when the list has no nodes — O(1)."""
        return self._size == 0

    def get_current(self) -> T | None:
        """Payload under the cursor, or ``None`` when empty — O(1)."""
        return self._current.song if self._current is not None else None

    def __len__(self) -> int:
        """``len(list)`` — O(1)."""
        return self._size

    def __iter__(self) -> Iterator[T]:
        """Iterate over payloads from head to tail — O(n)."""
        node = self._head
        while node is not None:
            yield node.song
            node = node.next

    def __contains__(self, item: object) -> bool:
        """Membership test by value — O(n)."""
        return any(item == song for song in self)

    def iter_nodes(self) -> Iterator[Node[T]]:
        """Iterate over nodes head → tail (used by the didactic view) — O(n)."""
        node = self._head
        while node is not None:
            yield node
            node = node.next

    def to_list(self) -> list[T]:
        """Snapshot as a Python ``list`` for serialisation/tests only — O(n).

        Never used as storage: the authoritative structure stays the chain of
        nodes.
        """
        return list(self)

    # --------------------------------------------------------------- insert

    def insert_at_beginning(self, song: T) -> Node[T]:
        """Insert before ``head`` — O(1). Empty list also sets ``tail``/``current``."""
        node = Node(song=song, previous=None, next=self._head)
        if self._head is None:
            self._tail = node
        else:
            self._head.previous = node
        self._head = node
        if self._current is None:
            self._current = node
        self._size += 1
        return node

    def insert_at_end(self, song: T) -> Node[T]:
        """Append after ``tail`` — O(1). Empty list also sets ``head``/``current``."""
        node = Node(song=song, previous=self._tail, next=None)
        if self._tail is None:
            self._head = node
        else:
            self._tail.next = node
        self._tail = node
        if self._current is None:
            self._current = node
        self._size += 1
        return node

    def insert_at(self, position: int, song: T) -> Node[T]:
        """Insert at ``position`` in ``0 .. size`` — O(n).

        ``0`` delegates to :meth:`insert_at_beginning`, ``size`` to
        :meth:`insert_at_end`. In between, the walk starts from the closer end,
        which is exactly the advantage of having two directions.
        """
        self._check_position(position, upper=self._size, allow_empty=True)
        if position == 0:
            return self.insert_at_beginning(song)
        if position == self._size:
            return self.insert_at_end(song)

        node_after = self._node_at(position)
        assert node_after.previous is not None
        node = Node(song=song, previous=node_after.previous, next=node_after)
        node_after.previous.next = node
        node_after.previous = node
        self._size += 1
        return node

    # --------------------------------------------------------------- remove

    def remove(self, item: T | Node[T]) -> T:
        """Remove by value or by node reference and return the payload.

        O(n) when a value is given (it must be searched), O(1) when the caller
        already holds the node.
        """
        node = item if isinstance(item, Node) else self._find_node(item)
        if node is None:
            raise ItemNotFoundError("song not found in the list")
        return self._unlink(node)

    def remove_at(self, position: int) -> T:
        """Remove the node at ``position`` and return its payload — O(n)."""
        self._check_position(position, upper=self._size - 1, allow_empty=False)
        node = self._node_at(position)
        return self._unlink(node)

    # ----------------------------------------------------------------- find

    def find(self, item: T) -> int | None:
        """Index of the first node whose payload equals ``item``, or ``None`` — O(n)."""
        for index, song in enumerate(self):
            if song == item:
                return index
        return None

    def find_by(self, predicate: Callable[[T], bool]) -> int | None:
        """Index of the first payload matching ``predicate``, or ``None`` — O(n)."""
        for index, song in enumerate(self):
            if predicate(song):
                return index
        return None

    # ------------------------------------------------------------- movement

    def move_next(self) -> bool:
        """Advance the cursor — O(1).

        Returns ``True`` when it moved. At ``tail`` returns ``False`` and keeps
        ``current`` unchanged (``PLAYLIST-009 = A``, ``PLAYLIST-009a``).
        """
        if self._current is None or self._current.next is None:
            return False
        self._current = self._current.next
        return True

    def move_previous(self) -> bool:
        """Move the cursor back — O(1).

        Returns ``True`` when it moved. At ``head`` returns ``False`` and keeps
        ``current`` unchanged (``PLAYLIST-009 = A``, ``PLAYLIST-009a``).
        """
        if self._current is None or self._current.previous is None:
            return False
        self._current = self._current.previous
        return True

    def move_to(self, position: int) -> T:
        """Point the cursor at ``position`` (select a song from the UI) — O(n).

        Returns the selected payload.
        """
        self._check_position(position, upper=self._size - 1, allow_empty=False)
        self._current = self._node_at(position)
        return self._current.song

    def clear(self) -> None:
        """Drop every node and reset the cursor — O(n).

        Links are cut explicitly so detached nodes are collectable immediately.
        """
        node = self._head
        while node is not None:
            following = node.next
            node.previous = None
            node.next = None
            node = following
        self._head = None
        self._tail = None
        self._current = None
        self._size = 0

    # ------------------------------------------------------------- internals

    def _find_node(self, item: T) -> Node[T] | None:
        """First node whose payload equals ``item`` — O(n)."""
        node = self._head
        while node is not None:
            if node.song == item:
                return node
            node = node.next
        return None

    def _node_at(self, position: int) -> Node[T]:
        """Node at ``position`` (``0 <= position < size``) — O(n), nearer end wins."""
        if position <= self._size // 2:
            node = self._head
            for _ in range(position):
                assert node is not None
                node = node.next
        else:
            node = self._tail
            for _ in range(self._size - 1 - position):
                assert node is not None
                node = node.previous
        assert node is not None
        return node

    def _unlink(self, node: Node[T]) -> T:
        """Detach ``node``, repair neighbours and move the cursor if needed — O(1).

        Cursor policy (``PLAYLIST-009b``): when the removed node is the current
        one, the cursor moves to the **next** node, or to the **previous** one
        when the node was the tail; removing the only node leaves it empty.
        """
        previous, following = node.previous, node.next

        if previous is None:
            self._head = following
        else:
            previous.next = following

        if following is None:
            self._tail = previous
        else:
            following.previous = previous

        if self._current is node:
            self._current = following if following is not None else previous

        node.previous = None
        node.next = None
        self._size -= 1
        return node.song

    def _check_position(self, position: int, *, upper: int, allow_empty: bool) -> None:
        """Validate ``0 <= position <= upper`` (or ``< upper`` semantics via caller)."""
        if not allow_empty and self._size == 0:
            raise EmptyPlaylistError("the list is empty")
        if position < 0 or position > upper:
            raise InvalidPositionError(position, self._size)

    # ----------------------------------------------------------- invariants

    def assert_invariants(self) -> None:
        """Raise ``AssertionError`` when an invariant is broken — O(n).

        Called after every operation in the test suite; it is the executable
        version of the invariant list in the class docstring.
        """
        assert (self._size == 0) == (self._head is None)
        assert (self._size == 0) == (self._tail is None)
        assert (self._size == 0) == (self._current is None)

        if self._head is not None:
            assert self._head.previous is None
        if self._tail is not None:
            assert self._tail.next is None

        count = 0
        node = self._head
        previous: Node[T] | None = None
        while node is not None:
            # Invariant 3, checked backwards while walking forwards.
            assert node.previous is previous
            previous = node
            count += 1
            node = node.next
            # A broken chain would loop forever; fail fast instead.
            assert count <= self._size

        # Invariant 4: exactly `size` nodes, ending on the tail.
        assert count == self._size
        assert previous is self._tail

        # Invariant 5: the cursor belongs to the list.
        if self._current is not None:
            assert any(node is self._current for node in self.iter_nodes())

    def __repr__(self) -> str:
        """Readable summary, e.g. ``DoublyLinkedList(size=3)``."""
        return f"{type(self).__name__}(size={self._size})"
