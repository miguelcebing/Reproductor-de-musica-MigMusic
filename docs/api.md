# MigMusic API

> Reference maintained by hand while the API grows (F3). OpenAPI docs are served
> at `/docs` in development and disabled in production (`APP_ENV=production`).
> Error mapping lives in
> [`error_handlers.py`](../backend/src/migmusic/api/error_handlers.py).

## Conventions

- Base path: `/api`
- All responses are JSON; durations are seconds, `duration_label` is `m:ss`.
- Errors use a single envelope:

```json
{
  "error": {
    "code": "not_found",
    "message": "playlist 42 not found",
    "request_id": "a1b2c3d4e5f6a7b8"
  }
}
```

- `request_id` is echoed from the `X-Request-ID` header when present, so logs
  on Render can be correlated with a browser request.
- Routers never `try/except`: domain exceptions are mapped once, centrally.
- State lives in memory for now (`InMemoryPlaylistRepository`); the SQL adapter
  arrives in F10 behind the same `PlaylistRepository` port.

## Endpoints

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness/readiness probe. Never touches Spotify or the database. |

**200**

```json
{ "status": "ok", "service": "migmusic", "environment": "development" }
```

---

### Playlists

`PlaylistOut` — `id`, `name`, `size`, `current_index`, `songs[]`.
`SongOut` — `id`, `title`, `artist`, `source`, `duration`, `duration_label`,
`album`, `artwork_url`, `external_url`, `available`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/playlists` | List every playlist with its songs in list order. |
| `POST` | `/api/playlists` | Create an empty playlist (`PLAYLIST-002`). Body: `{"name": "Queue"}` |
| `GET` | `/api/playlists/{id}` | Read one playlist. `404` for unknown ids. |
| `PATCH` | `/api/playlists/{id}` | Rename (`PLAYLIST-003`). Body: `{"name": "New"}` |
| `DELETE` | `/api/playlists/{id}` | Delete. `204`, empty body. |
| `POST` | `/api/playlists/{id}/songs` | Append, or insert at `index` (`UX-003`). Returns the playlist. |
| `DELETE` | `/api/playlists/{id}/songs/{index}` | Remove a song; returns the removed song (`PLAYLIST-009b`). |
| `PUT` | `/api/playlists/{id}/songs/order` | Move `from_index` → `to_index` (`FEAT-001-e`). |
| `POST` | `/api/playlists/{id}/songs/{index}/select` | Activate the playlist, move the cursor, return the playback state. |

**Append a song**

```json
POST /api/playlists/{id}/songs
{
  "song": {
    "id": "local-1",
    "title": "Nocturne",
    "artist": "Chopin",
    "source": "local",
    "duration": 305.0
  },
  "index": 1
}
```

`index` is optional; omit it to append at the tail. `source` is one of
`local` / `spotify`.

---

### Playback

One active playlist at a time. `PlaybackOut` — `playlist_id`, `song`,
`index`, `position`, `playing`, `repeat`, `shuffle`, `size`,
`available_next`, `available_previous`, `skip_seconds`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/playback` | Current transport state. `404 not_found` when nothing is open. |
| `POST` | `/api/playback/open` | Activate a playlist at its first song. Body: `{"playlist_id": "..."}` |
| `POST` | `/api/playback/next` | Step forward; stops (`playing: false`) at the tail (`PLAYLIST-009 = A`). |
| `POST` | `/api/playback/previous` | Step back; stays put at the head unless `repeat=all`. |
| `POST` | `/api/playback/finished` | The player reports the song ended; advances, or restarts under `repeat=one`. |
| `POST` | `/api/playback/skip` | Move exactly `skip_seconds`. Body: `{"direction": "forward"}` or `"backward"` (`PLAYER-001/002`). |
| `POST` | `/api/playback/seek` | Jump inside the song. Body: `{"position": 42.5}` (`PLAYER-007`). |
| `POST` | `/api/playback/report` | Frontend reports what it observes; only the given fields change (`PLAYER-011`). |
| `POST` | `/api/playback/modes` | Toggle `repeat` (`off` / `one` / `all`) and `shuffle` (`FEAT-001-d`, `PLAYER-004`). |

**Notes**

- The server owns the transport: `skip` and `seek` are validated against the
  song duration before anything moves; impossible positions answer `422`.
- `skip` backward at `position <= skip_seconds` goes to the previous song and
  resets the clock to `0.0` (`PLAYER-002a`).
- `shuffle` permutes an internal playback order; the playlist itself never
  reorders, so the queue the user sees stays intact.
- `seek` is clamped to `0 .. duration` and `duration` may be `0` (unknown),
  in which case only `>= 0` is enforced.

---

## Status codes

| Code | Meaning |
|---|---|
| 400 | Domain rule violated (`DomainError`) |
| 404 | Entity not found (`NotFoundError`), including "no active playback" |
| 422 | Request body failed validation (`request_validation_error`), or a domain rule (`validation_error`) |
| 502/503 | Upstream failure (Spotify, database) |
| 500 | Unhandled error; details only in the logs |
