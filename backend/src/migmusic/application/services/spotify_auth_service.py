"""Spotify auth use cases: login URL, callback exchange, refresh, logout."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx

from migmusic.core import ValidationError
from migmusic.domain.ports.token_store import TokenBundle, TokenStore
from migmusic.infrastructure.spotify.spotify_oauth import SpotifyOAuth, TokenResponse


class SpotifyAuthError(ValidationError):
    """Raised when the OAuth handshake fails (bad state, revoked token, ...)."""


@dataclass(slots=True, frozen=True)
class ValidAccessToken:
    """An access token that is guaranteed not to expire for the next minute."""

    access_token: str
    expires_in: int


class SpotifyAuthService:
    """Orchestrates the OAuth flow: login URL, callback, refresh, logout.

    All secrets stay inside this service; the API layer only ever sees
    session ids and (on demand) a short-lived access token for the SDK.
    """

    # Refresh proactively so playback never dies mid-track.
    REFRESH_MARGIN_SECONDS = 60.0

    def __init__(
        self,
        oauth: SpotifyOAuth,
        token_store: TokenStore,
        http_client: httpx.AsyncClient,
    ) -> None:
        self._oauth = oauth
        self._tokens = token_store
        self._http = http_client

    def login_parts(self) -> tuple[str, str, str]:
        """Return ``(auth_url, state, code_verifier)`` for the redirect."""
        parts = self._oauth.build_authorization_url()
        return parts.url, parts.state, parts.code_verifier

    async def handle_callback(
        self,
        *,
        code: str,
        state: str,
        expected_state: str,
        code_verifier: str,
        session_id: str,
    ) -> None:
        """Validate ``state`` (anti-CSRF), exchange the code, persist tokens."""
        if state != expected_state:
            raise SpotifyAuthError("OAuth state mismatch; possible CSRF")
        tokens = await self._oauth.exchange_code(code, code_verifier, self._http)
        await self._store(session_id, tokens)

    async def valid_access_token(self, session_id: str) -> ValidAccessToken | None:
        """Return a token valid for at least a minute, refreshing when needed.

        Returns ``None`` when the session has no tokens or the refresh failed
        (revoked session) — the caller then reports "reconnect".
        """
        bundle = await self._tokens.get(session_id)
        if bundle is None:
            return None

        now = time.time()
        if bundle.expires_at - self.REFRESH_MARGIN_SECONDS > now:
            return ValidAccessToken(
                access_token=bundle.access_token,
                expires_in=max(1, int(bundle.expires_at - now)),
            )

        refreshed = await self._refresh(session_id, bundle)
        if refreshed is None:
            await self._tokens.delete(session_id)
            return None
        await self._store(session_id, refreshed)
        return ValidAccessToken(
            access_token=refreshed.access_token,
            expires_in=max(1, int(refreshed.expires_at - time.time())),
        )

    async def is_authenticated(self, session_id: str) -> bool:
        """Whether the session currently holds tokens (without refreshing)."""
        return await self._tokens.get(session_id) is not None

    async def logout(self, session_id: str) -> None:
        """Forget the tokens bound to ``session_id``."""
        await self._tokens.delete(session_id)

    async def _store(self, session_id: str, tokens: TokenResponse) -> None:
        await self._tokens.set(
            session_id,
            TokenBundle(
                access_token=tokens.access_token,
                refresh_token=tokens.refresh_token,
                expires_at=tokens.expires_at,
                scope=tokens.scope,
            ),
        )

    async def _refresh(self, session_id: str, old: TokenBundle) -> TokenResponse | None:
        """Single refresh attempt; failures propagate as ``None`` (revoked)."""
        del session_id  # kept for API symmetry with future audit logging
        try:
            return await self._oauth.refresh_token(old.refresh_token, self._http)
        except Exception:
            return None
