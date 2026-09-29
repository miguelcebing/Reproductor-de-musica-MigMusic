# MigMusic API

> Auto-generated reference while the API grows (F3). OpenAPI docs are served at
> `/docs` in development and disabled in production (`APP_ENV=production`).
> Response times and error envelope: see [`error_handlers.py`](../backend/src/migmusic/api/error_handlers.py).

## Conventions

- Base path: `/api`
- All responses are JSON; timestamps are ISO-8601 UTC.
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

## Status codes

| Code | Meaning |
|---|---|
| 400 | Domain rule violated (`DomainError`) |
| 404 | Entity not found (`NotFoundError`) |
| 422 | Request body failed validation, or a domain `ValidationError` |
| 502/503 | Upstream failure (Spotify, database) |
| 500 | Unhandled error; details only in the logs |
