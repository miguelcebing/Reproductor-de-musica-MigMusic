"""Tests for the security middleware (`SEC-001`)."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from migmusic.core import Settings
from migmusic.main import create_app


def make_app(settings: Settings, **overrides: Any) -> TestClient:
    """Build a client with a freshly configured app (no shared limiter state)."""
    from pydantic import SecretStr

    config = settings.model_copy(update=overrides)
    # model_copy bypasses validators, so SecretStr overrides must be explicit.
    for key, value in overrides.items():
        if key.endswith("secret_key") or key.endswith("client_secret"):
            setattr(config, key, SecretStr(value))
    return TestClient(create_app(config))


def test_expensive_routes_answer_429_after_the_budget(settings: Settings) -> None:
    client = make_app(settings, rate_limit_expensive_per_minute=2)
    headers = {"X-Device-Id": "device-a"}

    first = client.get("/api/youtube/search", params={"q": "a"}, headers=headers)
    second = client.get("/api/youtube/search", params={"q": "b"}, headers=headers)
    third = client.get("/api/youtube/search", params={"q": "c"}, headers=headers)

    assert first.status_code != 429
    assert second.status_code != 429
    assert third.status_code == 429
    assert int(third.headers["retry-after"]) >= 1
    assert third.json()["error"]["code"] == "rate_limited"


def test_the_budget_is_per_device_not_global(settings: Settings) -> None:
    client = make_app(settings, rate_limit_default_per_minute=1, rate_limit_expensive_per_minute=1)

    client.get("/api/playlists", headers={"X-Device-Id": "device-a"})
    blocked = client.get("/api/playlists", headers={"X-Device-Id": "device-a"})
    other = client.get("/api/playlists", headers={"X-Device-Id": "device-b"})

    assert blocked.status_code == 429
    assert other.status_code != 429


def test_health_is_never_rate_limited(settings: Settings) -> None:
    client = make_app(settings, rate_limit_default_per_minute=1)

    for _ in range(5):
        response = client.get("/api/health")

    assert response.status_code == 200


def test_rate_limiting_can_be_disabled(settings: Settings) -> None:
    client = make_app(settings, rate_limit_enabled=False, rate_limit_default_per_minute=1)

    for _ in range(5):
        response = client.get("/api/playlists", headers={"X-Device-Id": "device-a"})

    assert response.status_code == 200


def test_oversized_bodies_are_rejected_with_413(settings: Settings) -> None:
    client = make_app(settings, max_request_body_bytes=1024)
    payload = {"name": "x" * 5000}

    response = client.post("/api/playlists", json=payload)

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_security_headers_are_present(settings: Settings) -> None:
    client = make_app(settings)

    response = client.get("/api/health")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert (
        response.headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
    )
    # HSTS only makes sense over HTTPS (development skips it, production adds it).
    assert ("strict-transport-security" in response.headers) is settings.is_production
