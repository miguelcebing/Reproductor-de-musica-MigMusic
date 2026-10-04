# ADR-003: Single-origin deployment

- **Status:** Accepted (superseded in implementation, see §Update)
- **Date:** 2026-09-28
- **Updated:** 2026-10-04 — the **principle** (one origin) is unchanged; the
  implementation moved from a Vercel rewrite to an Nginx reverse proxy on AWS
  (`DEPLOY-006`).
- **Related:** `DEPLOY-001`, `DEPLOY-002`, `DEPLOY-006`, `SPOTIFY-003`,
  `SPOTIFY-004`, `CONS-005`

## Context

Only free tiers were allowed (`CONS-005`). Serving the static frontend and the
Python API from two different domains forces `SameSite=None` cookies, CORS with
credentials and two Redirect URIs to configure. A **single origin** avoids all
three: the cookie is `first-party` and the OAuth round-trip stays on one host.

## Decision (unchanged)

Serve the SPA and the API from **one origin**, with `/api/*` reaching the
backend and everything else falling back to the SPA's `index.html`.

### Implementation history

**2026-09-28 — Vercel rewrite (original).** Frontend on Vercel, API on Render,
joined by a rewrite:

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://migmusic-api.onrender.com/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

The second rewrite was the SPA catch-all (without it the OAuth callback answered
`404`); `/api/*` matched first. `x-vercel-enable-rewrite-caching: 0` was
mandatory because Vercel caches rewrites by default since 2026-04-06. Production
Redirect URI: `https://migmusic.vercel.app/api/auth/callback`.

**2026-10-04 — Nginx reverse proxy (current).** The Render free tier slept and
the GitHub `keep-alive` cron was unreliable, so both the cold start and the
external dependency were removed by moving to an always-on EC2 instance
(`DEPLOY-006`). The single origin is now provided by Nginx on the same server:

```nginx
server_name migmusicreproductor.duckdns.org;

location /api/   { proxy_pass http://migmusic_api; }   # Gunicorn 127.0.0.1:8000
location = /health { proxy_pass http://migmusic_api; }
location /       { try_files $uri $uri/ /index.html; } # SPA catch-all
```

- The page-level CSP and gzip moved from `vercel.json` into the Nginx vhost.
- Nginx forwards `X-Forwarded-Proto` / `X-Forwarded-For`, so redirects and
  `Secure` cookies still see the real scheme and client.
- Production Redirect URI:
  `https://migmusicreproductor.duckdns.org/api/auth/callback`.
- Development: `http://127.0.0.1:5173/callback` (Spotify rejects `localhost`
  since 2025-11-27).

## Consequences

- **One origin is preserved in both topologies**, so the cookie/CORS reasoning
  never changed; only the component doing the proxying did (Vercel → Nginx).
- The API is no longer exposed on a public hostname of its own: it binds to
  `127.0.0.1:8000` and is reachable only through Nginx, which also enforces the
  per-IP rate limits and the `client_max_body_size` cap.
- No cold start and no `keep-alive` cron: the server is always on, so
  `SPEED-FIX` / `WARM-FIX` workarounds and the Render self-ping are retired
  (`RENDER_BACKEND_URL` stays empty in production).
- HTTPS is provided by Let's Encrypt through `certbot --nginx`, renewed
  automatically by `certbot.timer`.
- The single server is now a single point of failure; the instance is covered by
  an AWS Budget with alerts at 5 and 10 USD/month and a nightly database backup.
