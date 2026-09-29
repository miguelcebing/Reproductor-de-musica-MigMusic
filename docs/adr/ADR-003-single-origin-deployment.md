# ADR-003: Single origin via Vercel rewrite proxy

- **Status:** Accepted
- **Date:** 2026-09-28
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
    { "source": "/api/(.*)", "destination": "/api" }
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
- Render sleeps on the free tier → an UptimeRobot ping every 5 min against
  `/api/health` avoids the first-request cold start.
