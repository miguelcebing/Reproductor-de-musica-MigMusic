"""Unit tests for the pending-login state: cookie, signed ``state``, fallback."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import Response
from starlette.requests import Request

from migmusic.api.spotify_session import (
    OAUTH_COOKIE,
    OauthState,
    read_oauth_cookie,
    resolve_oauth_state,
    sign_oauth_state,
    write_oauth_cookie,
)
from migmusic.core import Settings, ValidationError
from migmusic.core.session import sign

SECRET = "test-session-secret"


def _request(settings: Settings, cookies: dict[str, str] | None = None) -> Request:
    """Bare ASGI request carrying the app's settings and optional cookies."""
    cookie_header = "; ".join(f"{key}={value}" for key, value in (cookies or {}).items())
    scope: dict[str, object] = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(b"cookie", cookie_header.encode())] if cookie_header else [],
        "query_string": b"",
        "app": SimpleNamespace(state=SimpleNamespace(settings=settings)),
    }
    return Request(scope)  # type: ignore[arg-type]


def _cookie_value(response: Response) -> str:
    """First ``name=value`` pair of the ``Set-Cookie`` header."""
    return response.headers["set-cookie"].split(";", 1)[0].split("=", 1)[1]


def test_signed_state_carries_the_pending_login(settings: Settings) -> None:
    """``state`` alone is enough to rebuild verifier + session id."""
    request = _request(settings)
    state = sign_oauth_state(request, code_verifier="verifier-1", session_id="session-1")

    assert resolve_oauth_state(request, state) == OauthState(
        state=state, code_verifier="verifier-1", session_id="session-1"
    )


def test_signed_state_survives_a_missing_cookie(settings: Settings) -> None:
    """The bug fix: a lost/expired ``mig_oauth`` cookie must not break the login."""
    signed = sign_oauth_state(
        _request(settings), code_verifier="verifier-1", session_id="session-1"
    )

    assert resolve_oauth_state(_request(settings), signed) is not None


def test_the_cookie_wins_when_it_matches(settings: Settings) -> None:
    """Browser-bound path: cookie and ``state`` agree, cookie is used."""
    request = _request(settings)
    state = sign_oauth_state(request, code_verifier="v", session_id="s")
    response = Response()
    write_oauth_cookie(response, request, state)

    from_cookie = _request(settings, {OAUTH_COOKIE: _cookie_value(response)})

    assert resolve_oauth_state(from_cookie, state) is not None
    assert read_oauth_cookie(from_cookie) is not None


def test_oauth_cookie_honours_the_configured_max_age(settings: Settings) -> None:
    """``OAUTH_STATE_MAX_AGE`` decides how long a login may stay unfinished."""
    request = _request(settings)
    state = sign_oauth_state(request, code_verifier="v", session_id="s")

    response = Response()
    write_oauth_cookie(response, request, state)

    assert f"Max-Age={settings.oauth_state_max_age}" in response.headers["set-cookie"]


def test_mismatched_cookie_and_state_is_a_csrf_rejection(settings: Settings) -> None:
    """A valid cookie plus an unverifiable ``state`` is never an anonymous user."""
    request = _request(settings)
    state = sign_oauth_state(request, code_verifier="v", session_id="s")
    tampered = _request(settings, {OAUTH_COOKIE: sign(f"other|{SECRET}", SECRET)})

    with pytest.raises(ValidationError, match="state mismatch"):
        resolve_oauth_state(tampered, f"{state}-forged")


def test_no_cookie_and_an_unsigned_state_is_rejected(settings: Settings) -> None:
    """Forged callbacks answer ``401`` (no pending login at all)."""
    assert resolve_oauth_state(_request(settings), "whatever") is None


def test_a_signed_payload_without_fields_is_rejected(settings: Settings) -> None:
    """Well-formed signature, wrong shape: treated as absent, never trusted."""
    assert resolve_oauth_state(_request(settings), sign("|", SECRET)) is None
    assert read_oauth_cookie(_request(settings, {OAUTH_COOKIE: sign("|", SECRET)})) is None
