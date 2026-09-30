"""Tests for the HMAC-signed cookie payload helper."""

from __future__ import annotations

from migmusic.core.session import sign, verify

SECRET = "test-session-secret"


def test_sign_verify_round_trip() -> None:
    """A signed value survives a round trip untouched."""
    signed = sign("state|verifier|session", SECRET)

    assert verify(signed, SECRET) == "state|verifier|session"


def test_verify_rejects_tampered_payload() -> None:
    """Changing any part of the payload invalidates the signature."""
    signed = sign("original-value", SECRET)
    payload, signature = signed.split(".")
    tampered = f"{payload}x.{signature}"

    assert verify(tampered, SECRET) is None


def test_verify_rejects_wrong_secret() -> None:
    """A signature made with another secret never verifies."""
    signed = sign("value", SECRET)

    assert verify(signed, "another-secret") is None


def test_verify_rejects_garbage_input() -> None:
    """Malformed input returns ``None`` instead of raising."""
    assert verify("not-a-signed-value", SECRET) is None
    assert verify("", SECRET) is None
    assert verify("only-payload", SECRET) is None


def test_sign_uses_urlsafe_base64() -> None:
    """The signature never contains characters a cookie cannot carry."""
    signed = sign("value with | and spaces", SECRET)

    assert "+" not in signed
    assert "/" not in signed
    assert "=" not in signed
