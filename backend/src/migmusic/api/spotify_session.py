"""Spotify session cookies: signing, reading and clearing.

Tokens live server-side in the ``TokenStore``; the browser only ever holds two
signed, ``HttpOnly`` cookies:

``mig_oauth``
    Short-lived carrier for ``state`` + ``code_verifier`` + session id while
    Spotify has the browser. Cleared on callback.
``mig_session``
    Opaque session id that keys the token store. Readable by the backend only.
"""

from __future__ import annotations

from typing import NamedTuple, cast

from fastapi import Response
from starlette.requests import Request

from migmusic.core import Settings
from migmusic.core.session import sign, verify

OAUTH_COOKIE = "mig_oauth"
SESSION_COOKIE = "mig_session"

OAUTH_MAX_AGE = 600  # 10 minutes to complete the redirect round-trip
SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days, refreshed on every login


class OauthState(NamedTuple):
    """Payload carried in the ``mig_oauth`` cookie."""

    state: str
    code_verifier: str
    session_id: str


def _is_production(request: Request) -> bool:
    settings = cast(Settings, request.app.state.settings)
    return settings.is_production


def write_oauth_cookie(response: Response, request: Request, payload: OauthState) -> None:
    """Attach the signed short-lived OAuth cookie to ``response``."""
    raw = f"{payload.state}|{payload.code_verifier}|{payload.session_id}"
    secret = request.app.state.settings.session_secret_key.get_secret_value()
    response.set_cookie(
        OAUTH_COOKIE,
        sign(raw, secret),
        max_age=OAUTH_MAX_AGE,
        httponly=True,
        secure=_is_production(request),
        samesite="lax",
        path="/",
    )


def read_oauth_cookie(request: Request) -> OauthState | None:
    """Parse and authenticate the OAuth cookie; ``None`` when absent/tampered."""
    raw = request.cookies.get(OAUTH_COOKIE)
    if not raw:
        return None
    secret = request.app.state.settings.session_secret_key.get_secret_value()
    value = verify(raw, secret)
    if value is None or value.count("|") != 2:
        return None
    state, verifier, session_id = value.split("|", 2)
    if not (state and verifier and session_id):
        return None
    return OauthState(state=state, code_verifier=verifier, session_id=session_id)


def read_session_id(request: Request) -> str | None:
    """Return the signed session id from the persistent cookie, if valid."""
    raw = request.cookies.get(SESSION_COOKIE)
    if not raw:
        return None
    secret = request.app.state.settings.session_secret_key.get_secret_value()
    return verify(raw, secret) or None


def write_session_cookie(
    response: Response, request: Request, session_id: str, *, max_age: int
) -> None:
    """Attach or refresh the signed session cookie."""
    secret = request.app.state.settings.session_secret_key.get_secret_value()
    response.set_cookie(
        SESSION_COOKIE,
        sign(session_id, secret),
        max_age=max_age,
        httponly=True,
        secure=_is_production(request),
        samesite="lax",
        path="/",
    )


def clear_oauth_cookie(response: Response, request: Request) -> None:
    """Expire the short-lived OAuth cookie."""
    response.delete_cookie(OAUTH_COOKIE, path="/", samesite="lax", secure=_is_production(request))


def clear_session_cookie(response: Response, request: Request) -> None:
    """Expire the session cookie on logout."""
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="lax", secure=_is_production(request))
