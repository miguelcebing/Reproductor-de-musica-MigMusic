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
    SESSION_MAX_AGE,
    OauthState,
    clear_oauth_cookie,
    clear_session_cookie,
    read_oauth_cookie,
    read_session_id,
    write_oauth_cookie,
    write_session_cookie,
)
from migmusic.application.services.spotify_auth_service import SpotifyAuthService

router = APIRouter(prefix="/api/auth/spotify", tags=["auth"])


@router.get("/login", summary="Start the Spotify OAuth flow", status_code=302)
async def login(request: Request, service: SpotifyAuthServiceDep) -> RedirectResponse:
    """Generate PKCE + state, stash them in a signed cookie, redirect to Spotify."""
    auth_url, state, code_verifier = service.login_parts()
    session_id = read_session_id(request) or secrets.token_urlsafe(24)

    response = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    write_oauth_cookie(
        response,
        request,
        OauthState(state=state, code_verifier=code_verifier, session_id=session_id),
    )
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
    """Validate the OAuth cookie and exchange the code; return the session id.

    Raises ``401`` when the short-lived cookie is missing or tampered with, so
    both callback flavours fail identically.
    """
    pending = read_oauth_cookie(request)
    if pending is None:
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
