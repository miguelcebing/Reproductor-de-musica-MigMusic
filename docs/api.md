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
`album`, `artwork_url`, `external_url`, `available`, `favorite`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/playlists` | List every playlist with its songs in list order. |
| `POST` | `/api/playlists` | Create an empty playlist (`PLAYLIST-002`). Body: `{"name": "Queue"}` |
| `GET` | `/api/playlists/{id}` | Read one playlist. `404` for unknown ids. |
| `PATCH` | `/api/playlists/{id}` | Rename (`PLAYLIST-003`). Body: `{"name": "New"}` |
| `DELETE` | `/api/playlists/{id}` | Delete. `204`, empty body. |
| `POST` | `/api/playlists/{id}/songs` | Append, or insert at `index` (`UX-003`). Returns the playlist. |
| `GET` | `/api/playlists/{id}/songs/find?text=…` | First song matching `text` (case-insensitive title/artist) + its index (`FEAT-001-c`). `404` on miss, `422` on blank. |
| `DELETE` | `/api/playlists/{id}/songs/{index}` | Remove a song; returns the removed song (`PLAYLIST-009b`). |
| `PUT` | `/api/playlists/{id}/songs/order` | Move `from_index` → `to_index` (`FEAT-001-e`). |
| `PUT` | `/api/playlists/{id}/songs/{index}/favorite` | Set `{"favorite": true}` / `{"favorite": false}`; returns the song (`FEAT-001-b`). |
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

### Spotify auth (`F6`)

OAuth **Authorization Code + PKCE**, executed entirely server-side
(`spotify_oauth.py`). The browser only ever talks to these routes; tokens are
stored backend-side under the session id (`SPOTIFY-007`, ADR-005).

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/auth/spotify/login` | `302` to `accounts.spotify.com/authorize`. Sets the short-lived `mig_oauth` cookie (state + PKCE verifier + session id). |
| `GET` | `/api/auth/spotify/callback` | **Production** Redirect URI. Exchanges the code, sets `mig_session`, redirects to the SPA. `401` when the state cookie is missing/tampered with. |
| `POST` | `/api/auth/spotify/callback` | **Development** variant: the SPA forwards the reply. Body: `{"code": "...", "state": "..."}` → `{"authenticated": true}`. |
| `GET` | `/api/auth/spotify/status` | `{"authenticated": true \| false}` — cheap link check for the UI. |
| `GET` | `/api/auth/spotify/token` | Fresh access token for the Web Playback SDK: `{"access_token": "...", "expires_in": 3600, "token_type": "Bearer"}`, `Cache-Control: no-store`. `401` when the session is missing or expired; **never** returns the refresh token. |
| `POST` | `/api/auth/spotify/logout` | Drops the stored tokens and expires `mig_session`. `204`. |

**Cookies** — `HttpOnly`, `SameSite=Lax`, `Secure` in production, `Path=/`:
`mig_oauth` (10 min, deleted on callback) and `mig_session` (30 days).

---

### Spotify catalog and player (`F6`)

All routes resolve a fresh access token per request (`SpotifyTokenDep`) and
proxy Spotify's Web API; nothing here talks to Spotify directly from the
browser. `SongOut` is the same shape as in *Playlists*, with
`source: "spotify"` and `id` equal to the Spotify track id.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/spotify/search` | `?q=…&limit=1..50` → `SongOut[]`. |
| `GET` | `/api/spotify/saved` | The user's saved tracks (`user-library-read`). |
| `GET` | `/api/spotify/playlists` | Playlist headers: `id`, `name`, `track_count`, `artwork_url`. |
| `GET` | `/api/spotify/playlists/{id}/tracks` | Tracks of one Spotify playlist (`?limit=1..100`). |
| `PUT` | `/api/spotify/player/play` | Queue playback. Body: `{"uris": ["spotify:track:…"], "device_id": "…", "position_ms": 0}`. `204`. |
| `PUT` | `/api/spotify/player/pause` | Pause (`device_id` optional). `204`. |
| `POST` | `/api/spotify/player/next` | Next track. `204`. |
| `POST` | `/api/spotify/player/previous` | Previous track. `204`. |
| `PUT` | `/api/spotify/player/seek` | Body: `{"position_ms": 12345}`. `204`. |
| `PUT` | `/api/spotify/player/volume` | Body: `{"volume_percent": 0..100}`. `204`. |
| `GET` | `/api/spotify/player/state` | `{"playing", "position_ms", "duration_ms", "track_uri", "volume_percent", "device_id"}`. `404` upstream means nothing is playing. |

**Notes**

- Every route answers `401` (`code: "http_error"`) when the session holds no
  Spotify tokens, so the frontend can re-run the login flow.
- `429` from Spotify (rate limit **or** `reason: "QUOTA_EXCEEDED"`, see
  ADR-005) propagates with `Retry-After` honoured once by the client.
- `5xx` from Spotify surface as `502/503`; `404`/`409` keep their status so
  "no active device" stays distinguishable.

---

## Status codes

| Code | Meaning |
|---|---|
| 400 | Domain rule violated (`DomainError`) |
| 404 | Entity not found (`NotFoundError`), including "no active playback" |
| 422 | Request body failed validation (`request_validation_error`), or a domain rule (`validation_error`) |
| 502/503 | Upstream failure (Spotify, database) |
| 500 | Unhandled error; details only in the logs |
