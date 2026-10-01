# ADR-003: Single origin via Vercel rewrite proxy

- **Status:** Accepted
- **Date:** 2026-09-28
- **Updated:** 2026-10-01 (catch-all rewrite, uvicorn `--proxy-headers`, keep-alive)
- **Related:** `DEPLOY-001`, `DEPLOY-002`, `SPOTIFY-003`, `SPOTIFY-004`,
  `CONS-005`

## Context

Only free tiers are allowed (`CONS-005`): static frontend on Vercel, Python
backend on Render. Splitting them across two domains forces `SameSite=None`
cookies, CORS with credentials, and two Redirect URIs to configure.

## Decision

Deploy the frontend on **Vercel** and the API on **Render**, but expose a
**single origin** by rewriting `/api/*` from Vercel to the Render service.

```json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://migmusic-api.onrender.com/api/$1" },
    { "source": "/(.*)", "destination": "/index.html" }
  ],
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        { "key": "x-vercel-enable-rewrite-caching", "value": "0" }
      ]
    }
  ]
}
```

The second rewrite is the SPA catch-all: without it, the OAuth callback path
answers `404` on Vercel instead of reaching the API, and deep links land on a
blank page. `/api/*` is matched first, so it always wins over `index.html`.

Production Redirect URI: `https://migmusic.vercel.app/api/auth/callback`.
Development: `http://127.0.0.1:5173/callback` (Spotify rejects `localhost`
since 2025-11-27).

## Consequences

- No cross-origin cookies and no CORS headaches in production; the browser
  only ever talks to `migmusic.vercel.app`.
- **`x-vercel-enable-rewrite-caching: 0` is mandatory.** Since 2026-04-06
  Vercel caches rewrites by default, which would serve stale API responses.
- The rewrite proxy inherits Vercel's 120 s timeout; long polling is not
  supported (not needed here).
- Uvicorn runs with `--proxy-headers --forwarded-allow-ips="*"` (`render.yaml`)
  so redirects and `Secure` cookies are built from the `X-Forwarded-*` values
  Vercel sends, not from the internal Render host.
- Render sleeps on the free tier → the `keep-alive` GitHub Actions workflow
  pings `/api/health` every 10 min (backend first, then the Vercel proxy) and
  doubles as a production monitor. It replaces the external UptimeRobot
  monitor, so no third-party service has to be kept configured.
