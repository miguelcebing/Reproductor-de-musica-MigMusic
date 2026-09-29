# ADR-001: Doubly linked list lives in the backend only

- **Status:** Accepted
- **Date:** 2026-09-28
- **Related:** `ARCH-001` (option A), `PLAYLIST-009`, `DB-003`

## Context

The player runs in the browser and local files must never be uploaded to the
server. The backend is Python. A doubly linked list could live in the backend,
in the frontend, or in both (AGEND.md §8.5).

## Decision

The `DoublyLinkedList` lives **only in the Python backend**. `next`,
`previous` and skip operations are HTTP calls; the backend owns the `current`
pointer.

The frontend keeps an ephemeral read-only mirror of the ordering purely to
render the didactic node view. It never mutates links.

## Consequences

- The academic requirement is met by real Python code with real
  `previous`/`next` references, explainable line by line during defence.
- Navigation costs one HTTP round trip. Acceptable for this scope (4-day
  deadline, `CONS-001`).
- Persistence maps links to `prev_id`/`next_id` columns and rebuilds the list
  on load (see ADR-004).
- Rejected alternatives: **B** (frontend-only) would reduce the Python backend
  to OAuth/persistence and lose academic weight; **C** (both with a shared
  contract) doubles maintenance for no gain at this scale.
