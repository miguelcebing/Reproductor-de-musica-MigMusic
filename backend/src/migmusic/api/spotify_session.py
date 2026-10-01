"""Spotify session cookies and the pending-login (OAuth) state.

Tokens live server-side in the ``TokenStore``; the browser only ever holds two
signed, ``HttpOnly`` cookies:

``mig_oauth``
    Short-lived carrier for the pending login while Spotify has the browser.
    Cleared on callback.
``mig_session``
    Opaque session id that keys the token store. Readable by the backend only.

The pending login is *not* bound to that cookie alone: :func:`sign_oauth_state`
produces an HMAC-signed blob of ``code_verifier|session_id`` that travels in the
``state`` query parameter as well. Spotify echoes ``state`` back untouched, so
the callback can rebuild the login even when the cookie never arrives (slow 2FA,
blocked third-party cookies, proxy rewrites). The cookie, when present, still
wins — that is the browser-bound, anti-CSRF path.
"""

from __future__ import annotations

from typing import Literal, NamedTuple, cast

from fastapi import Response
from starlette.requests import Request

from migmusic.core import Settings, ValidationError
from migmusic.core.session import sign, verify

OAUTH_COOKIE = "mig_oauth"
SESSION_COOKIE = "mig_session"

SESSION_MAX_AGE = 60 * 60 * 24 * 30  # 30 days, refreshed on every login

# The pending login payload is ``code_verifier|session_id`` inside sign().
_PAYLOAD_SEPARATOR = "|"
_PAYLOAD_FIELDS = 1  # number of separators expected


class OauthState(NamedTuple):
    """A pending Spotify login.

    ``state`` is the signed blob itself: it is both the cookie value and the
    ``state`` query parameter, so the two can never disagree.
    """

    state: str
    code_verifier: str
    session_id: str


def _settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


def _secret(request: Request) -> str:
    return _settings(request).session_secret_key.get_secret_value()


def _samesite(request: Request) -> Literal["lax", "none"]:
    """``none`` in production (frontend and API live on different domains)."""
    return "none" if _settings(request).is_production else "lax"


def _secure(request: Request) -> bool:
    return _settings(request).is_production


def _oauth_max_age(request: Request) -> int:
    """Seconds a login may stay unfinished (``OAUTH_STATE_MAX_AGE``)."""
    return _settings(request).oauth_state_max_age


def sign_oauth_state(request: Request, *, code_verifier: str, session_id: str) -> str:
    """Sign a self-contained pending login for the ``state`` query parameter."""
    payload = f"{code_verifier}{_PAYLOAD_SEPARATOR}{session_id}"
    return sign(payload, _secret(request))


def _decode_state(request: Request, raw: str | None) -> OauthState | None:
    """Unpack a signed pending login; ``None`` when absent, old or tampered."""
    if not raw:
        return None
    payload = verify(raw, _secret(request))
    if payload is None or payload.count(_PAYLOAD_SEPARATOR) != _PAYLOAD_FIELDS:
        return None
    code_verifier, session_id = payload.split(_PAYLOAD_SEPARATOR, _PAYLOAD_FIELDS)
    if not (code_verifier and session_id):
        return None
    return OauthState(state=raw, code_verifier=code_verifier, session_id=session_id)


def write_oauth_cookie(response: Response, request: Request, state: str) -> None:
    """Park the signed pending login in the short-lived ``mig_oauth`` cookie.

    ``state`` must come from :func:`sign_oauth_state`; it is stored verbatim so
    cookie and ``state`` query parameter always carry the same signed value.
    """
    response.set_cookie(
        OAUTH_COOKIE,
        state,
        max_age=_oauth_max_age(request),
        httponly=True,
        path="/",
        samesite=_samesite(request),
        secure=_secure(request),
    )


def read_oauth_cookie(request: Request) -> OauthState | None:
    """Parse and authenticate the OAuth cookie; ``None`` when absent/tampered."""
    return _decode_state(request, request.cookies.get(OAUTH_COOKIE))


def resolve_oauth_state(request: Request, state: str) -> OauthState | None:
    """Rebuild the pending login from the callback's ``state``.

    Preference order:

    1. the ``mig_oauth`` cookie when it matches ``state`` (browser-bound);
    2. the signature carried by ``state`` itself (cookie lost or expired);
    3. ``None`` → the caller answers ``401`` and the user logs in again.

    Raises ``ValidationError`` (→ ``422``) when a valid cookie is present but
    the callback carries a different, unverifiable ``state``: that is a CSRF
    attempt or a corrupted redirect, never an anonymous visitor.
    """
    pending = read_oauth_cookie(request)
    if pending is not None and pending.state == state:
        return pending
    from_state = _decode_state(request, state)
    if from_state is not None:
        return from_state
    if pending is not None:
        raise ValidationError("OAuth state mismatch; possible CSRF")
    return None


def read_session_id(request: Request) -> str | None:
    """Return the signed session id from the persistent cookie, if valid."""
    raw = request.cookies.get(SESSION_COOKIE)
    if not raw:
        return None
    return verify(raw, _secret(request)) or None


def write_session_cookie(
    response: Response, request: Request, session_id: str, *, max_age: int
) -> None:
    """Attach or refresh the signed session cookie."""
    response.set_cookie(
        SESSION_COOKIE,
        sign(session_id, _secret(request)),
        max_age=max_age,
        httponly=True,
        path="/",
        samesite=_samesite(request),
        secure=_secure(request),
    )


def clear_oauth_cookie(response: Response, request: Request) -> None:
    """Expire the short-lived OAuth cookie."""
    response.delete_cookie(
        OAUTH_COOKIE,
        path="/",
        samesite=_samesite(request),
        secure=_secure(request),
    )


def clear_session_cookie(response: Response, request: Request) -> None:
    """Expire the session cookie on logout."""
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        samesite=_samesite(request),
        secure=_secure(request),
    )
