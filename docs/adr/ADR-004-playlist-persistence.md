# ADR-004: Playlist order persisted as `prev_id` / `next_id`

- **Status:** Accepted
- **Date:** 2026-09-28
- **Related:** `DB-001`, `DB-002`, `DB-003` (option B), `PLAYLIST-001`

## Context

PostgreSQL on Neon stores playlists (`DB-001`, `DB-002`). A linked list has no
relational equivalent, so its order must be encoded somehow: neighbour pointers,
a plain `position` integer, or something else (`DB-003`).

## Decision

Store **both** neighbour pointers and an ordering fallback:

| Column | Meaning |
|---|---|
| `prev_id` | `NULL` on the head, otherwise the previous track |
| `next_id` | `NULL` on the tail, otherwise the next track |
| `position` | dense integer used to rebuild deterministically if pointers are inconsistent |

The `DoublyLinkedList` is **reconstructed on every load**: rows are sorted by
`position`, then `previous`/`next` links are re-created and `current` is reset
to the head (or to a stored `current_position`).

The domain stays free of any ORM: `SqlPlaylistRepository` (infrastructure)
maps rows back to `Playlist` entities and implements the `PlaylistRepository`
port.

## Consequences

- The stored shape mirrors the in-memory structure, which makes the
  reconstruction step easy to explain during the defence.
- `NULL` at both ends encodes stop-at-the-edges semantics directly
  (`PLAYLIST-009 = A`); no circular behaviour to enforce at the DB level.
- Insert/remove in the middle requires updating up to four rows
  (`prev`/`next` of the neighbours plus the new row). Wrapped in a transaction.
- `position` is a safety net: if pointers are ever inconsistent, an ordering
  repair pass can rebuild the list without data loss.
- Rejected: **position only** — cheap writes but every navigation needs a
  sorted read; **nested sets** — over-engineered for a linear playlist.
