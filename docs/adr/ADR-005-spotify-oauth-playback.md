# ADR-005: Spotify OAuth, session and playback (F6)

- **Status:** Accepted
- **Date:** 2026-09-28
- **Related:** `SPOTIFY-001`…`SPOTIFY-008`, `F6-STATE`, `F6-SCOPES`,
  `DEPLOY-001`, `DEPLOY-002`, ADR-003

## Context

`SKILL3` (`spotify-integration`) obliges us to verify Spotify's **current**
documentation before coding, because Redirect URI rules, allowed flows and
quota modes keep changing. Findings below were checked against the official
docs on 2026-09-28.

## Findings (official documentation, checked 2026-09-28)

| Topic | Current rule | Source |
|---|---|---|
| Redirect URIs | HTTPS mandatory **except** loopback IP literals (`http://127.0.0.1:PORT`, `http://[::1]:PORT`). **`localhost` is not allowed.** Exact string match; only loopback may vary the port. Enforced for apps created since 2025-04-09, migrated by 2025-11. | *Redirect URIs* |
| Flows | Implicit Grant is deprecated; new clients must use **Authorization Code with PKCE**. Confidential clients must use PKCE too. | *Increasing the security requirements…* (2025-02-12) |
| Dev mode | New Development-Mode apps (since 2026-02-11, all apps from 2026-03-09): owner needs an **active Premium** subscription, **≤ 5 authorized users** per Client ID, ≤ 25 Client IDs per developer account (since 2026-07), quota counted **per developer account**. `429` may carry `reason: "QUOTA_EXCEEDED"`. | *Quota modes*, *Feb 2026 migration guide*, *Web API quota updates* (2026-07-23) |
| Extended quota | Reserved for established, scalable use cases (since 2025-05-15); only organizations are accepted. Irrelevant for this academic project. | *Updating the Criteria for Web API Extended Access* |
| Web Playback SDK | Client-side library that creates a local Spotify Connect device. Requires **Premium** (mobile-only Premium types excluded). Needs the **`streaming`** scope. `getOAuthToken` is called on `connect()` and whenever the token expires (max 60 min). `account_error` fires for non-Premium users. | *Web Playback SDK*, *Scopes* |
| `getOAuthToken` | Must resolve with a valid `access_token` for a Premium user; tokens last ~1 h. | *Web Playback SDK Reference* |

## Decision

1. **Flow:** Authorization Code + **PKCE (S256)** against
   `accounts.spotify.com`, always executed **server-side** in FastAPI
   (`spotify_oauth.py`): `state` anti-CSRF, `code_verifier` never leaves the
   backend.
2. **Redirect URIs (two, one per environment):**
   - Development: `http://127.0.0.1:5173/callback` (loopback literal → HTTP
     allowed). The SPA forwards `code`/`state` to
     `POST /api/auth/spotify/callback`.
   - Production: `https://migmusic.vercel.app/api/auth/callback`
     (ADR-003 single origin). The backend exchanges the code and redirects
     the browser back to the SPA.
3. **Session (`F6-STATE`):** tokens live **only** in the backend
   (`TokenStore` keyed by session id). The browser holds two `HttpOnly`
   cookies signed with HMAC-SHA256: `mig_oauth` (10 min, PKCE state +
   session id, cleared on callback) and `mig_session` (30 d, session id).
   `SameSite=Lax` (same-origin in both environments), `Secure` when
   `APP_ENV=production`. The access token is refreshed server-side ~60 s
   before expiry; if the refresh fails the session is dropped and the UI
   asks the user to reconnect (`SPOTIFY-007`).
4. **SDK token:** `GET /api/auth/spotify/token` returns a *fresh* access
   token (`Cache-Control: no-store`) to the Web Playback SDK's
   `getOAuthToken`. The refresh token and the Client Secret are **never**
   sent to the frontend.
5. **Scopes (`F6-SCOPES`, `SPOTIFY-006` option C):** `streaming`,
   `user-read-email`, `user-read-private`, `user-read-playback-state`,
   `user-modify-playback-state`, `playlist-read-private`,
   `user-library-read`, `user-follow-read`.
6. **Playback:** the SDK creates the device; the backend proxy
   (`PUT /api/spotify/player/play` with `device_id` + `uris`) starts the
   track, so every Spotify call stays behind our Python layer. SDK state
   (`player_state_changed` + polling `getCurrentState`) drives the UI.

## Consequences

- **Development mode is a real constraint:** only 5 authorized users and the
  app owner must keep Premium active; without it the whole app stops working
  during the demo window. Extended quota mode is out of reach for this
  project.
- Quota errors arrive as `429` with `reason: "QUOTA_EXCEEDED"` (since
  2026-07); our client already honours `Retry-After`, but a quota 429 should
  not be retried in a loop — the current single retry keeps that bounded.
- The SPA needs a dedicated `/callback` route because development and
  production use different Redirect URI shapes.
- Web Playback SDK limits stand: no playback speed control, no access to raw
  audio (no visualizer/EQ on Spotify sources), Premium required, and no
  gapless playback when switching between local and Spotify sources.
- CSP must allow `https://sdk.scdn.co` (script) and the Spotify connect
  endpoints used by the SDK.
