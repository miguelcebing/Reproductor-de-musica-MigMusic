# ADR-002: Hexagonal layered architecture with dependency injection

- **Status:** Accepted
- **Date:** 2026-09-28
- **Related:** `ARCH-002`, `BACK-001`, `BACK-003`

## Context

The project is graded on architecture (POO, SOLID, separation of concerns) and
also ships as a real product. The framework (`FastAPI`) must not leak into the
business rules.

## Decision

```
api  ──▶  application  ──▶  domain  ◀──  infrastructure
                              ▲
                     core (config, logging, base errors)
```

- `domain` — pure Python: entities, `Node`/`DoublyLinkedList`, ports (`ABC`),
  domain exceptions. No FastAPI, no ORM, no `os.environ`, no HTTP.
- `application` — use cases (`PlaylistService`, `PlaybackService`,
  `SpotifyAuthService`) that receive ports through constructors.
- `infrastructure` — adapters implementing those ports (Spotify, SQL and
  in-memory repositories, token store).
- `api` — thin routers: HTTP ⇄ DTO ⇄ use case only.
- `core` — `Settings`, JSON logging, base exception hierarchy.
- `main.py` is the **composition root**: the only place where concrete
  implementations are instantiated and wired.

## Consequences

- Ports can be swapped (`InMemoryPlaylistRepository` ⇄ `SqlPlaylistRepository`)
  without touching services (Liskov, Dependency Inversion).
- Testing is straightforward: services take fakes, the API takes a
  `TestClient`.
- Routers never `try/except`: a single `error_handlers.py` maps domain
  exceptions to HTTP (SOLID, single responsibility).
- `ruff` + strict `mypy` enforce the boundary mechanically in CI.
