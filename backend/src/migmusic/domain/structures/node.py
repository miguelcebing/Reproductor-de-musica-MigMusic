"""One link of the chain.

A node knows only its payload and its two neighbours; it never walks the list
itself. That is what makes ``previous``/``next`` cheap in both directions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(slots=True)
class Node(Generic[T]):
    """A node holding a song (``Song`` in production, any value in tests).

    Attributes:
        song: Payload carried by this node.
        previous: Node before this one, or ``None`` for the head.
        next: Node after this one, or ``None`` for the tail (``PLAYLIST-009 = A``).
    """

    song: T
    previous: Node[T] | None = None
    next: Node[T] | None = None
