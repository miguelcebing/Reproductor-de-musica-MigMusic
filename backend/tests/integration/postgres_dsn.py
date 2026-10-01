"""Shared PostgreSQL lookup for the SQL adapter contract tests.

``TEST_DATABASE_URL`` wins (CI, or a developer pointing at Neon); otherwise the
embedded ``pgserver`` dev dependency boots a throwaway server — no Docker
(``DEPLOY-004``) required. Empty string means "no database available" and the
contract tests skip themselves.
"""

from __future__ import annotations

import atexit
import os
import tempfile
from pathlib import Path

try:  # Embedded PostgreSQL; absent only in environments that override the DSN.
    import pgserver
except ImportError:  # pragma: no cover - depends on the environment
    pgserver = None  # type: ignore[assignment]


def resolve_dsn() -> str:
    """Return the DSN to test against, or ``""`` when PostgreSQL is unavailable."""
    provided = os.environ.get("TEST_DATABASE_URL", "")
    if provided:
        return provided
    if pgserver is None:  # pragma: no cover - depends on the environment
        return ""
    try:
        data_dir = Path(tempfile.gettempdir()) / "migmusic-test-pg"
        server = pgserver.get_server(str(data_dir))
        atexit.register(server.cleanup)
        return server.get_uri()
    except Exception:  # pragma: no cover - skip instead of failing collection
        return ""


DSN = resolve_dsn()
