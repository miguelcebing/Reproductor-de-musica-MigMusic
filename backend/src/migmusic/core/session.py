"""HMAC-signed cookie values (stdlib only).

Used to carry the OAuth ``state``/``code_verifier`` across the redirect and the
opaque session id that keys the server-side ``TokenStore``. The signature makes
tampering detectable without a session database.
"""

from __future__ import annotations

import base64
import hashlib
import hmac

_SEPARATOR = "."


def sign(value: str, secret: str) -> str:
    """Return ``base64url(value)`` appended with its HMAC-SHA256 signature."""
    payload = base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    signature = base64.urlsafe_b64encode(digest).decode().rstrip("=")
    return f"{payload}{_SEPARATOR}{signature}"


def verify(signed: str, secret: str) -> str | None:
    """Return the original value when the signature is valid, else ``None``."""
    try:
        payload, signature = signed.rsplit(_SEPARATOR, 1)
    except ValueError:
        return None

    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    given = _b64decode(signature)
    if given is None or not hmac.compare_digest(expected, given):
        return None

    decoded = _b64decode(payload)
    if decoded is None:
        return None
    return decoded.decode()


def _b64decode(value: str) -> bytes | None:
    """Decode base64url with padding restored; return ``None`` on garbage."""
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (ValueError, TypeError):
        return None
