"""Translate domain exceptions into HTTP responses.

Routers stay free of try/except: every exception mapping lives here.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from migmusic.core import DomainError, ExternalServiceError, NotFoundError, ValidationError

# Domain error class -> (HTTP status, machine-readable code)
_DOMAIN_STATUS: dict[type[BaseException], tuple[int, str]] = {
    NotFoundError: (404, "not_found"),
    ValidationError: (422, "validation_error"),
    DomainError: (400, "bad_request"),
}


def _payload(request: Request, status_code: int, code: str, detail: Any) -> dict[str, Any]:
    """Build the uniform error body returned by the API."""
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:16]
    return {
        "error": {
            "code": code,
            "message": str(detail),
            "request_id": request_id,
        }
    }


def _status_for(exc: BaseException) -> tuple[int, str]:
    """Resolve the mapping for ``exc``, walking its MRO so subclasses inherit."""
    for candidate in type(exc).__mro__:
        mapped = _DOMAIN_STATUS.get(candidate)
        if mapped is not None:
            return mapped
    return 400, "domain_error"  # pragma: no cover - unreachable: DomainError always maps


def register_error_handlers(app: FastAPI) -> None:
    """Attach the single mapping from exceptions to HTTP responses."""

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        status_code, code = _status_for(exc)
        return JSONResponse(
            status_code=status_code,
            content=_payload(request, status_code, code, exc),
        )

    @app.exception_handler(ExternalServiceError)
    async def handle_external_service_error(
        request: Request, exc: ExternalServiceError
    ) -> JSONResponse:
        upstream_status = exc.status_code if exc.status_code is not None else 502
        status_code = upstream_status if 400 <= upstream_status < 600 else 502
        # The client only gets "{service} unavailable"; the upstream detail
        # ("Invalid limit", "rate limited"...) is what the logs need.
        request.app.state.logger.warning(
            "upstream_error service=%s status=%s detail=%s", exc.service, status_code, exc
        )
        return JSONResponse(
            status_code=status_code,
            content=_payload(request, status_code, "upstream_error", f"{exc.service} unavailable"),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_request_validation(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=_payload(request, 422, "request_validation_error", exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_payload(request, exc.status_code, "http_error", exc.detail),
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        # Never leak internals to the client; the full traceback goes to the logs.
        request.app.state.logger.exception("unhandled_exception")
        return JSONResponse(
            status_code=500,
            content=_payload(request, 500, "internal_error", "Unexpected server error"),
        )
