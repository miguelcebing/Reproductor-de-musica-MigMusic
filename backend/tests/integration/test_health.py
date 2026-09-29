"""Tests for the health endpoint and error mapping."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_returns_ok(client: TestClient) -> None:
    """The probe answers 200 without touching Spotify or the database."""
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "migmusic"
    assert body["environment"] == "development"


def test_unknown_route_returns_structured_error(client: TestClient) -> None:
    """404s follow the uniform error envelope."""
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "http_error"
    assert error["request_id"]


def test_cors_allows_the_frontend_origin(client: TestClient) -> None:
    """Preflight requests from the configured frontend origin are accepted."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:5173"
