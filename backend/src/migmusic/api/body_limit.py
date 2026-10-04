"""Request-body size guard (`SEC-001`).

Playlist and lyrics payloads are small; a request that declares a larger body
is rejected with ``413`` before Starlette reads it into memory, which keeps a
crafted upload from exhausting the free-tier instance.
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp


class MaxBodySizeMiddleware(BaseHTTPMiddleware):
    """Reject bodies whose declared ``Content-Length`` exceeds the limit."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        super().__init__(app)
        self._max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        # Only bodies matter; GET/DELETE (no body) never pay for this.
        if request.method in {"POST", "PUT", "PATCH"}:
            declared = request.headers.get("content-length")
            if declared is not None:
                try:
                    size = int(declared)
                except ValueError:
                    size = 0
                if size > self._max_bytes:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": {
                                "code": "payload_too_large",
                                "message": (
                                    f"Request body exceeds the {self._max_bytes}-byte limit."
                                ),
                                "request_id": "",
                            }
                        },
                    )
        return await call_next(request)


__all__ = ["MaxBodySizeMiddleware"]
