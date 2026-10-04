"""In-process rate limiting (`SEC-001`).

Counts requests in a sliding window keyed by the anonymous ``X-Device-Id``
(one bucket per user) and falls back to the client IP for keyless routes
(webhooks, OAuth callbacks). The Vercel proxy hides the real client IP, so the
device id is the reliable key and the IP is only a secondary defence.

The store is a plain dict: Render's free plan runs a single instance, so a
process-local limiter is enough; a multi-instance deploy would need Redis.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp

from migmusic.api.dependencies import DEVICE_ID_HEADER

WINDOW_SECONDS = 60.0

# Routes that call an external service (catalog, lyrics): the strict bucket.
_EXPENSIVE_PREFIXES = ("/api/spotify/search", "/api/youtube/search", "/api/lyrics")
# Auth and other abuse-prone routes get their own budget.
_AUTH_PREFIXES = ("/api/auth/",)


@dataclass(frozen=True, slots=True)
class RateLimitRule:
    """A named budget: ``limit`` requests per ``window`` seconds."""

    name: str
    limit: int


def rule_for(path: str, limits: RateLimits) -> RateLimitRule:
    """Pick the bucket a request path belongs to."""
    if path.startswith(_EXPENSIVE_PREFIXES):
        return RateLimitRule("expensive", limits.expensive)
    if path.startswith(_AUTH_PREFIXES):
        return RateLimitRule("auth", limits.auth)
    return RateLimitRule("default", limits.default)


@dataclass(frozen=True, slots=True)
class RateLimits:
    """Per-minute budgets resolved from settings."""

    default: int
    expensive: int
    auth: int


class RateLimiter:
    """Sliding-window counter with one deque per (rule, key)."""

    def __init__(self, limits: RateLimits, *, window: float = WINDOW_SECONDS) -> None:
        self._limits = limits
        self._window = window
        self._buckets: dict[tuple[str, str], deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, rule: RateLimitRule, key: str, *, now: float | None = None) -> float | None:
        """Return ``None`` when allowed, or the seconds to wait when limited."""
        moment = time.monotonic() if now is None else now
        cutoff = moment - self._window
        with self._lock:
            bucket = self._buckets.setdefault((rule.name, key), deque())
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= rule.limit:
                retry_after = max(1, int(self._window - (moment - bucket[0])) + 1)
                return float(retry_after)
            bucket.append(moment)
            return None

    def reset(self) -> None:
        """Drop every bucket (tests)."""
        with self._lock:
            self._buckets.clear()


def client_key(request: Request) -> str:
    """Identify the caller: device id first, client IP as the fallback."""
    device_id = request.headers.get(DEVICE_ID_HEADER, "").strip()
    if device_id:
        return f"device:{device_id[:128]}"
    client = request.client
    return f"ip:{client.host}" if client else "ip:unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Reject over-budget requests with ``429`` and a clear envelope."""

    def __init__(self, app: ASGIApp, *, limiter: RateLimiter, enabled: bool = True) -> None:
        super().__init__(app)
        self._limiter = limiter
        self._enabled = enabled

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        if not self._enabled:
            return await call_next(request)
        # Health checks must never be throttled: the platform and the keep-alive
        # loop depend on them.
        path = request.url.path
        if path == "/api/health":
            return await call_next(request)

        rule = rule_for(path, self._limiter._limits)
        retry_after = self._limiter.check(rule, client_key(request))
        if retry_after is not None:
            return _too_many_requests(retry_after)
        return await call_next(request)


def _too_many_requests(retry_after: float) -> JSONResponse:
    """Uniform ``429`` body matching the API error envelope."""
    seconds = int(retry_after)
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": str(seconds)},
        content={
            "error": {
                "code": "rate_limited",
                "message": (f"Too many requests; slow down and try again in {seconds} second(s)."),
                "request_id": "",
            }
        },
    )


__all__ = [
    "RateLimitMiddleware",
    "RateLimitRule",
    "RateLimiter",
    "RateLimits",
    "client_key",
    "rule_for",
]
