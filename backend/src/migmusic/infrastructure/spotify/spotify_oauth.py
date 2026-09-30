"""Spotify OAuth: PKCE, state, token exchange, refresh (``SKILL3``)."""

import base64
import hashlib
import secrets
import time
from dataclasses import dataclass
from typing import Literal

import httpx

from migmusic.core import SpotifyConfig, ValidationError


@dataclass(slots=True, frozen=True)
class AuthURLParts:
    """Parts needed to build the Spotify authorization URL."""

    url: str
    state: str
    code_verifier: str


@dataclass(slots=True, frozen=True)
class TokenResponse:
    """Result of a successful token exchange."""

    access_token: str
    token_type: Literal["Bearer"]
    expires_in: int
    refresh_token: str
    scope: str

    @property
    def expires_at(self) -> float:
        return time.time() + self.expires_in - 30  # 30 s buffer


class SpotifyOAuthError(ValidationError):
    """Errors during the OAuth flow (invalid state, bad code, etc.).

    The ``code`` field keeps the machine-readable OAuth error identifier while
    the message stays human-readable for logs and API responses.
    """

    def __init__(self, code: str, detail: str = "") -> None:
        message = f"Spotify OAuth error [{code}]"
        if detail:
            message = f"{message}: {detail}"
        super().__init__(message)
        self.code = code
        self.detail = detail


class SpotifyOAuth:
    """Generates PKCE/state, builds auth URLs, exchanges codes, refreshes tokens."""

    TOKEN_URL = "https://accounts.spotify.com/api/token"  # noqa: S105 - public endpoint
    AUTH_URL = "https://accounts.spotify.com/authorize"

    def __init__(self, config: SpotifyConfig) -> None:
        self._config = config

    def build_authorization_url(self) -> AuthURLParts:
        """Generate PKCE code_verifier/challenge and a random state."""
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = self._pkce_challenge(code_verifier)
        state = secrets.token_urlsafe(24)

        params = {
            "response_type": "code",
            "client_id": self._config.client_id,
            "redirect_uri": self._config.redirect_uri,
            "scope": self._config.scopes,
            "state": state,
            "code_challenge_method": "S256",
            "code_challenge": code_challenge,
            "show_dialog": "false",
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return AuthURLParts(
            url=f"{self.AUTH_URL}?{query}",
            state=state,
            code_verifier=code_verifier,
        )

    async def exchange_code(
        self,
        code: str,
        code_verifier: str,
        client: httpx.AsyncClient,
    ) -> TokenResponse:
        """Exchange authorization code for access/refresh tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self._config.redirect_uri,
            "code_verifier": code_verifier,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }
        return await self._post_token(data, client)

    async def refresh_token(
        self,
        refresh_token: str,
        client: httpx.AsyncClient,
    ) -> TokenResponse:
        """Refresh an expired access token using the refresh token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self._config.client_id,
            "client_secret": self._config.client_secret,
        }
        return await self._post_token(data, client)

    @staticmethod
    def _pkce_challenge(verifier: str) -> str:
        """S256 code challenge: base64url(SHA256(verifier))."""
        digest = hashlib.sha256(verifier.encode()).digest()
        return base64.urlsafe_b64encode(digest).decode().rstrip("=")

    async def _post_token(self, data: dict[str, str], client: httpx.AsyncClient) -> TokenResponse:
        try:
            response = await client.post(
                self.TOKEN_URL,
                data=data,
                headers={"content-type": "application/x-www-form-urlencoded"},
                timeout=10.0,
            )
        except httpx.RequestError as exc:
            raise SpotifyOAuthError("network_error", f"Token request failed: {exc}") from exc

        if response.status_code == 400:
            raise SpotifyOAuthError("invalid_grant", response.text)
        if response.status_code == 401:
            raise SpotifyOAuthError("invalid_client", "Invalid client credentials")
        if response.status_code >= 500:
            raise SpotifyOAuthError("upstream_error", "Spotify token endpoint unavailable")

        try:
            payload = response.json()
        except ValueError as exc:
            raise SpotifyOAuthError("malformed_response", "Spotify returned non-JSON") from exc

        if "error" in payload:
            raise SpotifyOAuthError(
                payload.get("error", "unknown"),
                payload.get("error_description", "Unknown error"),
            )

        return TokenResponse(
            access_token=payload["access_token"],
            token_type=payload["token_type"],
            expires_in=int(payload["expires_in"]),
            refresh_token=payload["refresh_token"],
            scope=payload["scope"],
        )
