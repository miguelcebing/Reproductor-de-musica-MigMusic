"""Spotify OAuth endpoints.

Two callback paths are supported because the registered Redirect URIs differ
per environment (``SPOTIFY-003``):

``GET  /api/auth/spotify/callback``
    Production: Spotify redirects straight to the API (``/api/auth/callback``
    behind the Vercel rewrite), which then bounces back to the SPA.
``POST /api/auth/spotify/callback``
    Development: Spotify redirects to ``/callback`` on the frontend origin and
    the SPA forwards ``code``/``state`` here as JSON.

Both paths share the same state validation and token exchange.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse

from migmusic.api.dependencies import SpotifyAuthServiceDep
from migmusic.api.schemas import AccessTokenOut, AuthStatusOut, CallbackBody, CallbackOut
from migmusic.api.spotify_session import (
    OAUTH_COOKIE,
    SESSION_MAX_AGE,
    OauthState,
    clear_oauth_cookie,
    clear_session_cookie,
    read_session_id,
    resolve_oauth_state,
    sign_oauth_state,
    write_oauth_cookie,
    write_session_cookie,
)
from migmusic.application.services.spotify_auth_service import SpotifyAuthService
from migmusic.core import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/auth/spotify", tags=["auth"])


@router.get("/login", summary="Start the Spotify OAuth flow", status_code=302)
async def login(request: Request, service: SpotifyAuthServiceDep) -> RedirectResponse:
    """Prepare PKCE, sign a self-contained state, redirect to Spotify.

    ``state`` carries the signed ``code_verifier`` + session id, so the callback
    does not depend on the short-lived cookie surviving the round-trip (slow 2FA,
    blocked third-party cookies, proxy rewrites).
    """
    code_verifier = service.new_code_verifier()
    session_id = read_session_id(request) or secrets.token_urlsafe(24)
    state = sign_oauth_state(request, code_verifier=code_verifier, session_id=session_id)
    auth_url = service.authorization_url(state=state, code_verifier=code_verifier)

    response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    write_oauth_cookie(response, request, state)
    return response


@router.get("/callback", summary="OAuth callback (production redirect URI)")
async def callback_get(
    request: Request,
    code: str,
    state: str,
    service: SpotifyAuthServiceDep,
) -> RedirectResponse:
    """Handle the callback in the backend, then send the browser to the SPA."""
    pending = await _exchange(request, service, code, state)

    response = RedirectResponse(
        url=request.app.state.settings.frontend_origin,
        status_code=status.HTTP_302_FOUND,
    )
    write_session_cookie(response, request, pending.session_id, max_age=SESSION_MAX_AGE)
    clear_oauth_cookie(response, request)
    return response


@router.get("/callback-legacy", summary="OAuth callback (legacy redirect URI without /spotify/)")
async def callback_get_legacy(
    request: Request,
    code: str,
    state: str,
    service: SpotifyAuthServiceDep,
) -> RedirectResponse:
    """Handle the callback for legacy redirect URI (/api/auth/callback)."""
    pending = await _exchange(request, service, code, state)

    response = RedirectResponse(
        url=request.app.state.settings.frontend_origin,
        status_code=status.HTTP_302_FOUND,
    )
    write_session_cookie(response, request, pending.session_id, max_age=SESSION_MAX_AGE)
    clear_oauth_cookie(response, request)
    return response


@router.post("/callback", summary="OAuth callback (development redirect URI)")
async def callback_post(
    request: Request,
    response: Response,
    body: CallbackBody,
    service: SpotifyAuthServiceDep,
) -> CallbackOut:
    """Exchange the code forwarded by the SPA in development."""
    pending = await _exchange(request, service, body.code, body.state)
    write_session_cookie(response, request, pending.session_id, max_age=SESSION_MAX_AGE)
    clear_oauth_cookie(response, request)
    return CallbackOut(authenticated=True)


@router.get("/status", summary="Whether the session is linked to Spotify")
async def auth_status(
    request: Request,
    service: SpotifyAuthServiceDep,
) -> AuthStatusOut:
    """Cheap check so the UI can show a login button or the linked account."""
    session_id = read_session_id(request)
    if session_id is None:
        return AuthStatusOut(authenticated=False)
    return AuthStatusOut(authenticated=await service.is_authenticated(session_id))


@router.get(
    "/token",
    summary="Fresh access token for the Web Playback SDK",
    response_model=AccessTokenOut,
)
async def access_token(
    request: Request, response: Response, service: SpotifyAuthServiceDep
) -> AccessTokenOut:
    """Return a token valid for the next minute (``Cache-Control: no-store``).

    The refresh token is never handed out; a missing or revoked session is a
    plain ``401`` so the frontend reconnects.
    """
    response.headers["Cache-Control"] = "no-store"
    session_id = read_session_id(request)
    token = await service.valid_access_token(session_id) if session_id else None
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Spotify session is missing or expired",
            headers={"Cache-Control": "no-store"},
        )
    return AccessTokenOut(
        access_token=token.access_token,
        expires_in=token.expires_in,
        token_type="Bearer",  # noqa: S106 - OAuth scheme name, not a secret
    )


@router.post("/logout", summary="Disconnect Spotify from this session", status_code=204)
async def logout(request: Request, service: SpotifyAuthServiceDep) -> Response:
    """Delete the stored tokens and expire the session cookie."""
    session_id = read_session_id(request)
    if session_id is not None:
        await service.logout(session_id)

    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookie(response, request)
    return response


async def _exchange(
    request: Request,
    service: SpotifyAuthService,
    code: str,
    state: str,
) -> OauthState:
    """Rebuild the pending login, then exchange the code; return its session id.

    The pending login comes from the OAuth cookie when it is present and matches
    ``state``, otherwise from the signature carried by ``state`` itself. Raises
    ``401`` when neither is available, and ``422`` on a state mismatch, so both
    callback flavours fail identically.
    """
    pending = resolve_oauth_state(request, state)
    if pending is None:
        logger.warning(
            "spotify_callback_rejected",
            extra={
                "oauth_cookie": "present" if request.cookies.get(OAUTH_COOKIE) else "absent",
                "state_len": len(state),
            },
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or expired OAuth state; start the login again",
        )

    await service.handle_callback(
        code=code,
        state=state,
        expected_state=pending.state,
        code_verifier=pending.code_verifier,
        session_id=pending.session_id,
    )
    return pending
