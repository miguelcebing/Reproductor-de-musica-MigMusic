# MigMusic — Architecture

> Source of truth for requirements and decisions: [`AGEND.md`](../AGEND.md).
> Architectural decisions are recorded as ADRs in [`docs/adr/`](adr/).

## 1. Overview

MigMusic is a web music player whose core data structure is a **doubly linked
list**. It plays **local files** (never uploaded to the server) and **Spotify**
tracks (OAuth + Web Playback SDK), persists playlists server-side, and exposes a
didactic node view for the academic defence.

```mermaid
flowchart LR
    subgraph Browser
        UI[React UI]
        LP[LocalAudioPlayer]
        SP[SpotifyPlayer]
        DLLREF[Read-only node view]
    end

    subgraph Vercel
        F[Static frontend]
        PX["/api/* rewrite<br/>(caching disabled)"]
    end

    subgraph Render
        API[FastAPI]
        SVC[PlaylistService<br/>PlaybackService]
        DLL[("DoublyLinkedList<br/>(single source of truth)")]
    end

    DB[(PostgreSQL · Neon)]

    UI --> F
    PX --> API
    API --> SVC
    SVC --> DLL
    SVC --> DB
    LP -.->|HTML5 audio| FS[(Local files)]
    SP -.->|Web Playback SDK| SK[Spotify]
```

## 2. Layers and dependency direction

```mermaid
flowchart TB
    api["api<br/>routers · schemas · DI · error handlers"] --> application
    application["application<br/>PlaylistService · PlaybackService · SpotifyAuthService"] --> domain
    infrastructure["infrastructure<br/>Spotify · repositories · token store"] --> domain
    core["core<br/>config · logging · base errors"] -.-> domain
    domain["domain<br/>Song · Playlist · Node · DoublyLinkedList · ports"]

    style domain fill:#1e6bff,stroke:#4338CA,color:#fff
    style core fill:#4338CA,stroke:#4338CA,color:#fff
```

| Layer | May import | Must never import |
|---|---|---|
| `domain` | Python standard library, typing | FastAPI, SQLAlchemy, `os.environ`, HTTP |
| `application` | `domain`, ports (`ABC`) | concrete adapters, routers |
| `infrastructure` | `domain`, third-party SDKs | `api`, `application` internals |
| `api` | `application`, Pydantic, FastAPI | `domain` internals bypassing services |
| `main.py` | everything (composition root) | — |

Enforced mechanically: `ruff` (import rules) + strict `mypy` run in CI.

## 3. Class diagram

```mermaid
classDiagram
    class Song {
        <<value object>>
        +str id
        +str title
        +str artist
        +AudioSourceType source
        +float duration
    }

    class AudioSourceType {
        <<enumeration>>
        LOCAL
        SPOTIFY
    }

    class Node {
        -Song song
        -Node previous
        -Node next
    }

    class DoublyLinkedList {
        -Node head
        -Node tail
        -Node current
        -int size
        +append(song)
        +insert_at(index, song)
        +remove_at(index)
        +move_to(index)
        +next() Song
        +previous() Song
    }

    class Playlist {
        +str id
        +str name
        -DoublyLinkedList songs
        +add(song)
        +remove(index)
    }

    class MusicProvider {
        <<abstract>>
        +search(query) List~Song~
        +play(song) PlaybackHandle
    }

    class PlaylistRepository {
        <<abstract>>
        +save(playlist)
        +find(id) Playlist
        +list_all() List~Playlist~
    }

    class TokenStore {
        <<abstract>>
        +store(user, tokens)
        +refresh(user) Tokens
        +revoke(user)
    }

    class PlaylistService {
        +create(name)
        +add(playlist_id, song)
        +insert_at(playlist_id, index, song)
        +remove_at(playlist_id, index)
        +move_to(playlist_id, index)
    }

    class PlaybackService {
        +next(playlist_id) Song
        +previous(playlist_id) Song
        +skip(playlist_id, seconds) Song
        +select(playlist_id, index) Song
    }

    Song "1" --> "0..*" Node : held by
    Node "1" --> "0..1" Node : previous
    Node "1" --> "0..1" Node : next
    Playlist "1" *-- "1" DoublyLinkedList : contains
    DoublyLinkedList "1" o-- "*" Node
    PlaylistService --> PlaylistRepository : uses
    PlaylistService --> Playlist
    PlaybackService --> Playlist
    MusicProvider <|.. SpotifyMusicProvider
    PlaylistRepository <|.. InMemoryPlaylistRepository
    PlaylistRepository <|.. SqlPlaylistRepository
    TokenStore <|.. SessionTokenStore
    Song --> AudioSourceType
```

## 4. Sequence — next track (option A: list lives in the backend)

```mermaid
sequenceDiagram
    actor U as User
    participant UI as React UI
    participant API as FastAPI
    participant PS as PlaybackService
    participant DLL as DoublyLinkedList
    participant DB as PostgreSQL

    U->>UI: press "Next"
    UI->>API: POST /api/playlists/{id}/next
    API->>PS: next(playlist_id)
    PS->>DB: load playlist (prev_id / next_id)
    DB-->>PS: ordered rows
    PS->>DLL: rebuild from rows
    PS->>DLL: current.next
    alt not at tail
        DLL-->>PS: next Song
        PS-->>API: Song DTO
        API-->>UI: 200 { song }
        UI->>UI: swap audio source, play
    else at tail (PLAYLIST-009 = A)
        DLL-->>PS: None
        PS-->>API: 204 No Content
        API-->>UI: 204 (playback stops)
    end
```

## 5. Persistence model

`DB-003 = B`: the linked order is stored as neighbour pointers, and the list is
reconstructed on load.

```mermaid
erDiagram
    PLAYLIST ||--o{ TRACK : contains
    TRACK {
        uuid id PK
        uuid playlist_id FK
        uuid prev_id FK "nullable - head"
        uuid next_id FK "nullable - tail"
        string song_id
        int position "rebuild fallback / ordering"
    }
```

`prev_id`/`next_id` are **nullable**: the head has `prev_id = NULL` and the tail
has `next_id = NULL`, which is exactly the stop-at-the-edges behaviour required
by `PLAYLIST-009 = A` (no circular list).

## 6. Key decisions

| Decision | ADR |
|---|---|
| Doubly linked list lives in the Python backend | [ADR-001](adr/ADR-001-doubly-linked-list-location.md) |
| Hexagonal layers + dependency injection | [ADR-002](adr/ADR-002-hexagonal-layered-architecture.md) |
| Single origin through a Vercel rewrite proxy | [ADR-003](adr/ADR-003-single-origin-deployment.md) |
| Playlist order persisted as `prev_id`/`next_id` | [ADR-004](adr/ADR-004-playlist-persistence.md) |

## 7. Design patterns in use

Strategy (audio sources) · Repository (persistence) · Factory (players and
providers) · Adapter (Spotify) · Observer (player state → UI) · Dependency
Injection (`main.py` composition root).
