"""Tests for the Spotify OAuth builder (PKCE, state, token exchange)."""

from __future__ import annotations

import asyncio
import base64
import hashlib
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from migmusic.core import Settings, SpotifyConfig
from migmusic.infrastructure.spotify.spotify_oauth import (
    SpotifyOAuth,
    SpotifyOAuthError,
)

CONFIG = SpotifyConfig(
    client_id="client-123",
    client_secret="secret-456",
    redirect_uri="http://127.0.0.1:5173/callback",
    scopes="streaming user-read-private",
)


def _oauth() -> SpotifyOAuth:
    return SpotifyOAuth(CONFIG)


def test_authorization_url_contains_required_parameters() -> None:
    """The redirect carries every parameter Spotify requires for PKCE."""
    parts = _oauth().build_authorization_url()

    query = parse_qs(urlparse(parts.url).query)
    assert query["response_type"] == ["code"]
    assert query["client_id"] == ["client-123"]
    assert query["redirect_uri"] == ["http://127.0.0.1:5173/callback"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"] == [parts.state]
    assert query["code_challenge"]  # derived from the verifier, never the secret


def test_code_challenge_is_base64url_sha256_of_the_verifier() -> None:
    """PKCE S256: challenge = BASE64URL(SHA256(verifier)) without padding."""
    parts = _oauth().build_authorization_url()
    challenge = parse_qs(urlparse(parts.url).query)["code_challenge"][0]

    expected = (
        base64.urlsafe_b64encode(hashlib.sha256(parts.code_verifier.encode()).digest())
        .decode()
        .rstrip("=")
    )
    assert challenge == expected


def test_state_and_verifier_are_unique_per_call() -> None:
    """Two logins never reuse the same CSRF state or verifier."""
    first = _oauth().build_authorization_url()
    second = _oauth().build_authorization_url()

    assert first.state != second.state
    assert first.code_verifier != second.code_verifier


def test_exchange_code_sends_pkce_and_client_credentials() -> None:
    """The token request carries the verifier and (server-side) secret."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(httpx.QueryParams(request.content.decode())))
        return httpx.Response(
            200,
            json={
                "access_token": "at-1",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "rt-1",
                "scope": "streaming",
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            tokens = await _oauth().exchange_code("code-1", "verifier-1", client)
        assert tokens.access_token == "at-1"
        assert tokens.refresh_token == "rt-1"

    asyncio.run(run())
    assert captured["grant_type"] == "authorization_code"
    assert captured["code"] == "code-1"
    assert captured["code_verifier"] == "verifier-1"
    assert captured["client_id"] == "client-123"
    assert captured["client_secret"] == "secret-456"


def test_refresh_token_uses_refresh_grant() -> None:
    """The refresh request identifies itself with ``refresh_token``."""
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(dict(httpx.QueryParams(request.content.decode())))
        return httpx.Response(
            200,
            json={
                "access_token": "at-2",
                "token_type": "Bearer",
                "expires_in": 3600,
                "refresh_token": "rt-2",
                "scope": "streaming",
            },
        )

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            tokens = await _oauth().refresh_token("rt-1", client)
        assert tokens.access_token == "at-2"

    asyncio.run(run())
    assert captured["grant_type"] == "refresh_token"
    assert captured["refresh_token"] == "rt-1"


@pytest.mark.parametrize(
    ("status_code", "body", "expected_code"),
    [
        (400, {"error": "invalid_grant"}, "invalid_grant"),
        (401, {"error": "invalid_client"}, "invalid_client"),
        (500, {"error": "server_error"}, "upstream_error"),
    ],
)
def test_token_endpoint_errors_are_mapped(
    status_code: int, body: dict[str, str], expected_code: str
) -> None:
    """Upstream failures surface as a typed OAuth error, never a crash."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json=body)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(SpotifyOAuthError) as excinfo:
                await _oauth().exchange_code("code", "verifier", client)
        assert excinfo.value.code == expected_code

    asyncio.run(run())


def test_malformed_json_response_is_an_oauth_error() -> None:
    """A non-JSON answer from Spotify is reported, not swallowed."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            with pytest.raises(SpotifyOAuthError) as excinfo:
                await _oauth().exchange_code("code", "verifier", client)
        assert excinfo.value.code == "malformed_response"

    asyncio.run(run())


def test_settings_expose_a_spotify_config(settings: Settings) -> None:
    """The composition root reads OAuth settings in one place."""
    spotify = settings.spotify

    assert spotify.client_id == "test-client-id"
    assert spotify.redirect_uri == "http://127.0.0.1:5173/callback"
    assert "streaming" in spotify.scopes
