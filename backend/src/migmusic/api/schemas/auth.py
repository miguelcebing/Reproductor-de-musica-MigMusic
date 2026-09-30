"""Spotify auth request/response models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class CallbackBody(BaseModel):
    """Body of ``POST /api/auth/spotify/callback`` (development redirect path).

    Spotify sends the browser to ``/callback`` on the frontend origin; the SPA
    forwards ``code``/``state`` here so the exchange stays server-side.
    """

    code: str = Field(min_length=1)
    state: str = Field(min_length=1)


class AuthStatusOut(BaseModel):
    """Whether the browser session currently holds Spotify tokens."""

    authenticated: bool


class AccessTokenOut(BaseModel):
    """A short-lived access token for the Web Playback SDK.

    The refresh token is never returned by this endpoint.
    """

    access_token: str
    expires_in: int
    token_type: Literal["Bearer"] = "Bearer"  # noqa: S105 - OAuth scheme name


class CallbackOut(BaseModel):
    """Result of a successful callback exchange."""

    authenticated: bool


__all__ = ["AccessTokenOut", "AuthStatusOut", "CallbackBody", "CallbackOut"]
