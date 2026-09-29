"""Structured logging setup.

Produces one JSON object per line so Render/Vercel can parse logs. Secrets are
never written: callers pass only identifiers and public values.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Keys that must never reach a log sink, whatever a caller passes in.
_SENSITIVE_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "access_token",
        "refresh_token",
        "client_secret",
        "authorization",
        "cookie",
        "set-cookie",
        "api_key",
        "session",
    }
)

_RESERVED = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "taskName",
        "message",
        "asctime",
    }
)


def _scrub(data: dict[str, Any]) -> dict[str, Any]:
    """Drop sensitive keys and coerce values to JSON-safe types."""
    clean: dict[str, Any] = {}
    for key, value in data.items():
        if key.lower() in _SENSITIVE_KEYS:
            clean[key] = "[redacted]"
        elif isinstance(value, (str, int, float, bool)) or value is None:
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean


class JsonFormatter(logging.Formatter):
    """Format records as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize ``record`` plus any extra fields passed to ``logger.info``."""
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(_scrub(payload), ensure_ascii=False)


def configure_logging(level: str = "INFO") -> None:
    """Install the JSON handler on the root logger (idempotent)."""
    root = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(numeric_level)

    # uvicorn attaches its own handlers; keep ours as the single sink.
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        named = logging.getLogger(logger_name)
        named.handlers = []
        named.propagate = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger, e.g. ``get_logger(__name__)``."""
    return logging.getLogger(name)
