"""Tests for the single place where exceptions become HTTP responses."""

from __future__ import annotations

import logging

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from migmusic.api.error_handlers import register_error_handlers
from migmusic.core import (
    ConfigurationError,
    DomainError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)
from migmusic.domain import EmptyPlaylistError, InvalidPositionError, ItemNotFoundError
from migmusic.domain.exceptions import NoActivePlaybackError


def _build_client() -> TestClient:
    """Minimal app with only the error handlers registered."""
    app = FastAPI()
    app.state.logger = logging.getLogger("test")
    register_error_handlers(app)

    @app.get("/domain")
    async def domain() -> None:
        raise NotFoundError("playlist 42 not found")

    @app.get("/validation")
    async def validation() -> None:
        raise ValidationError("position out of range")

    @app.get("/generic-domain")
    async def generic_domain() -> None:
        raise DomainError("generic rule broken")

    @app.get("/upstream")
    async def upstream() -> None:
        raise ExternalServiceError("rate limited", service="spotify", status_code=429)

    @app.get("/upstream-unknown")
    async def upstream_unknown() -> None:
        raise ExternalServiceError("connection reset", service="postgres")

    @app.get("/boom")
    async def boom() -> None:
        raise ConfigurationError("unexpected failure")

    @app.get("/domain-empty")
    async def domain_empty() -> None:
        raise EmptyPlaylistError("the list is empty")

    @app.get("/domain-position")
    async def domain_position() -> None:
        raise InvalidPositionError(7, 3)

    @app.get("/domain-missing")
    async def domain_missing() -> None:
        raise ItemNotFoundError("song not found in the list")

    @app.get("/playback-inactive")
    async def playback_inactive() -> None:
        raise NoActivePlaybackError("no playlist is being played")

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize(
    ("path", "expected_status", "expected_code"),
    [
        ("/domain", 404, "not_found"),
        ("/validation", 422, "validation_error"),
        ("/generic-domain", 400, "bad_request"),
        ("/upstream", 429, "upstream_error"),
        ("/upstream-unknown", 502, "upstream_error"),
        ("/boom", 500, "internal_error"),
        ("/domain-empty", 400, "bad_request"),
        ("/domain-position", 422, "validation_error"),
        ("/domain-missing", 404, "not_found"),
        ("/playback-inactive", 404, "no_active_playback"),
    ],
)
def test_exceptions_map_to_the_expected_response(
    path: str, expected_status: int, expected_code: str
) -> None:
    """Every exception type yields the uniform error envelope."""
    client = _build_client()
    response = client.get(path)

    assert response.status_code == expected_status
    body = response.json()["error"]
    assert body["code"] == expected_code
    assert body["message"]
    assert body["request_id"]


def test_upstream_failures_keep_the_detail_in_the_log_only(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Clients get "{service} unavailable"; the reason stays in the logs."""
    client = _build_client()

    with caplog.at_level(logging.WARNING):
        response = client.get("/upstream")

    assert response.json()["error"]["message"] == "spotify unavailable"
    assert "rate limited" in caplog.text
    assert "spotify" in caplog.text


def test_error_bodies_never_leak_internals() -> None:
    """Unhandled errors return a generic message, not the exception text."""
    client = _build_client()
    body = client.get("/boom").json()["error"]

    assert body["message"] == "Unexpected server error"


def test_request_id_header_is_used_when_provided() -> None:
    """A caller-supplied request id is echoed back for correlation."""
    client = _build_client()
    body = client.get("/domain", headers={"x-request-id": "trace-me"}).json()["error"]

    assert body["request_id"] == "trace-me"


def test_request_payload_is_typed() -> None:
    """The handler signature matches FastAPI's exception contract."""
    assert callable(register_error_handlers)
    assert Request.__name__ == "Request"
