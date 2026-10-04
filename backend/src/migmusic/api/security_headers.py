"""Security response headers (`SEC-001`).

The API answers JSON and is consumed by the frontend through a same-origin
proxy, so the headers here harden API responses (no sniffing, HSTS, no framing,
no referrer leakage). The page-level Content-Security-Policy lives in Vercel's
``vercel.json`` because the HTML is served by the CDN, not by this app.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

# One year, including subdomains: the site is HTTPS-only on every platform.
_HSTS = "max-age=31536000; includeSubDomains"

_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": _HSTS,
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    # API responses are JSON or empty; no scripts, no framing, no form posts.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach the hardened headers to every response."""

    def __init__(self, app: ASGIApp, *, https_only: bool = True) -> None:
        super().__init__(app)
        self._https_only = https_only

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        for name, value in _HEADERS.items():
            if name == "Strict-Transport-Security" and not self._https_only:
                continue
            if name not in response.headers:
                response.headers[name] = value
        return response


__all__ = ["SecurityHeadersMiddleware"]
