"""Tests for the Spotify OAuth endpoints (login, callback, token, logout)."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from fastapi.testclient import TestClient

from migmusic.api.spotify_session import OAUTH_COOKIE, SESSION_COOKIE
from migmusic.core import Settings
from migmusic.core.session import sign

SECRET = "test-session-secret"


def _state_from(redirect_url: str) -> str:
    """Read the ``state`` Spotify will echo back."""
    return parse_qs(urlparse(redirect_url).query)["state"][0]


def test_login_redirects_to_spotify_with_pkce(
    spotify_client: TestClient, spotify_stub: object
) -> None:
    """The entry point answers a redirect and parks the state in a cookie."""
    response = spotify_client.get("/api/auth/spotify/login", follow_redirects=False)

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("https://accounts.spotify.com/authorize")
    query = parse_qs(urlparse(location).query)
    assert query["code_challenge_method"] == ["S256"]
    assert query["client_id"] == ["test-client-id"]
    assert response.cookies.get(OAUTH_COOKIE)


def test_callback_without_pending_login_is_rejected(spotify_client: TestClient) -> None:
    """A forged callback with no OAuth cookie never exchanges the code."""
    response = spotify_client.get(
        "/api/auth/spotify/callback?code=abc&state=whatever",
        follow_redirects=False,
    )

    assert response.status_code == 401
    assert response.json()["error"]["request_id"]


def test_callback_with_wrong_state_is_rejected(spotify_client: TestClient) -> None:
    """The state must match the one parked in the cookie (anti-CSRF)."""
    login = spotify_client.get("/api/auth/spotify/login", follow_redirects=False)
    real_state = _state_from(login.headers["location"])

    response = spotify_client.get(
        f"/api/auth/spotify/callback?code=abc&state={real_state}-forged",
        follow_redirects=False,
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_callback_completes_without_the_oauth_cookie(spotify_client: TestClient) -> None:
    """A lost/expired ``mig_oauth`` cookie must not break the callback.

    Slow 2FA or consent screens, blocked third-party cookies and proxy rewrites
    all drop that cookie: the signed ``state`` Spotify echoes back carries the
    same pending login, so the round-trip still succeeds.
    """
    login = spotify_client.get("/api/auth/spotify/login", follow_redirects=False)
    state = _state_from(login.headers["location"])
    assert spotify_client.cookies.get(OAUTH_COOKIE)  # sanity: the cookie was set
    spotify_client.cookies.clear()  # simulate it never arriving at the callback

    response = spotify_client.get(
        f"/api/auth/spotify/callback?code=abc&state={state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert spotify_client.cookies.get(SESSION_COOKIE)
    assert spotify_client.get("/api/auth/spotify/status").json() == {"authenticated": True}


def test_callback_accepts_a_state_from_a_second_login(spotify_client: TestClient) -> None:
    """Two tabs may start a login; the older ``state`` stays redeemable."""
    first = spotify_client.get("/api/auth/spotify/login", follow_redirects=False)
    first_state = _state_from(first.headers["location"])
    second = spotify_client.get("/api/auth/spotify/login", follow_redirects=False)
    second_state = _state_from(second.headers["location"])

    assert first_state != second_state
    assert spotify_client.cookies.get(OAUTH_COOKIE) == second_state

    response = spotify_client.get(
        f"/api/auth/spotify/callback?code=abc&state={first_state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert spotify_client.get("/api/auth/spotify/status").json() == {"authenticated": True}


def test_get_callback_sets_the_session_and_redirects_home(spotify_client: TestClient) -> None:
    """Production flow: Spotify lands on the API, which returns the SPA."""
    login = spotify_client.get("/api/auth/spotify/login", follow_redirects=False)
    state = _state_from(login.headers["location"])

    response = spotify_client.get(
        f"/api/auth/spotify/callback?code=abc&state={state}",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["location"] == "http://127.0.0.1:5173"
    assert spotify_client.cookies.get(SESSION_COOKIE)
    assert spotify_client.cookies.get(OAUTH_COOKIE) is None
    assert spotify_client.get("/api/auth/spotify/status").json() == {"authenticated": True}


def test_post_callback_supports_the_development_redirect(spotify_client: TestClient) -> None:
    """Development flow: the SPA forwards code/state as JSON."""
    login = spotify_client.get("/api/auth/spotify/login", follow_redirects=False)
    state = _state_from(login.headers["location"])

    response = spotify_client.post(
        "/api/auth/spotify/callback", json={"code": "abc", "state": state}
    )

    assert response.status_code == 200
    assert response.json() == {"authenticated": True}
    assert spotify_client.get("/api/auth/spotify/status").json() == {"authenticated": True}


def test_callback_requests_tokens_from_spotify(
    spotify_client: TestClient, spotify_stub: object
) -> None:
    """The code is exchanged server-side; the client secret never leaves."""
    login = spotify_client.get("/api/auth/spotify/login", follow_redirects=False)
    state = _state_from(login.headers["location"])

    spotify_client.get(f"/api/auth/spotify/callback?code=abc&state={state}", follow_redirects=False)

    token_requests = spotify_stub.token_requests
    assert len(token_requests) == 1
    body = token_requests[0].content.decode()
    assert "code=abc" in body
    assert "code_verifier=" in body
    assert "grant_type=authorization_code" in body


def test_status_is_false_for_anonymous_visitors(spotify_client: TestClient) -> None:
    """No cookie means no session."""
    response = spotify_client.get("/api/auth/spotify/status")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_status_is_false_for_a_tampered_cookie(spotify_client: TestClient) -> None:
    """A cookie signed with another secret is treated as absent."""
    spotify_client.cookies.set(SESSION_COOKIE, sign("session-1", "wrong-secret"))

    response = spotify_client.get("/api/auth/spotify/status")

    assert response.json() == {"authenticated": False}


def test_status_is_true_when_tokens_are_stored(linked_client: TestClient) -> None:
    """A valid session cookie plus stored tokens reads as connected."""
    response = linked_client.get("/api/auth/spotify/status")

    assert response.json() == {"authenticated": True}


def test_token_requires_a_linked_session(spotify_client: TestClient) -> None:
    """Anonymous callers get a plain 401 so the UI can prompt to sign in."""
    response = spotify_client.get("/api/auth/spotify/token")

    assert response.status_code == 401
    assert response.headers.get("cache-control") == "no-store"


def test_token_returns_a_bearer_token_without_the_refresh_token(
    linked_client: TestClient,
) -> None:
    """The SDK may see the access token; the refresh token never leaves."""
    response = linked_client.get("/api/auth/spotify/token")

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "access-token-1"
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] > 0
    assert "refresh" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_logout_clears_the_session(linked_client: TestClient) -> None:
    """Logging out revokes the server-side tokens and the cookie."""
    assert linked_client.get("/api/auth/spotify/status").json()["authenticated"] is True

    response = linked_client.post("/api/auth/spotify/logout")

    assert response.status_code == 204
    assert linked_client.get("/api/auth/spotify/status").json()["authenticated"] is False


def test_login_is_available_in_the_documented_scope(settings: Settings) -> None:
    """Guard against accidentally widening the requested scopes."""
    assert "streaming" in settings.spotify.scopes
    assert "user-modify-playback-state" in settings.spotify.scopes
    assert "playlist-read-private" in settings.spotify.scopes
    assert "user-library-read" in settings.spotify.scopes
