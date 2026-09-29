"""Tests for the structured JSON logger."""

from __future__ import annotations

import json
import logging

from migmusic.core.logging import JsonFormatter, configure_logging, get_logger


def _record(**extra: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="migmusic.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="something happened",
        args=(),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_format_emits_one_json_object_per_line() -> None:
    """Each record becomes a single parseable JSON line."""
    payload = json.loads(JsonFormatter().format(_record()))

    assert payload["level"] == "INFO"
    assert payload["logger"] == "migmusic.test"
    assert payload["message"] == "something happened"
    assert payload["timestamp"].endswith("+00:00")


def test_extra_fields_are_included() -> None:
    """Fields passed via ``extra=`` reach the payload."""
    payload = json.loads(JsonFormatter().format(_record(request_id="abc123")))

    assert payload["request_id"] == "abc123"


def test_sensitive_keys_are_redacted() -> None:
    """Secrets are never written to the log sink."""
    payload = json.loads(
        JsonFormatter().format(
            _record(
                access_token="spotify-token-value",
                password="hunter2",
                playlist_id="pl-1",
            )
        )
    )

    assert payload["access_token"] == "[redacted]"
    assert payload["password"] == "[redacted]"
    assert payload["playlist_id"] == "pl-1"
    assert "spotify-token-value" not in json.dumps(payload)


def test_non_scalar_values_are_stringified() -> None:
    """Values that JSON cannot encode are converted to strings."""
    payload = json.loads(JsonFormatter().format(_record(cors_origins={"a", "b"})))

    assert isinstance(payload["cors_origins"], str)


def test_configure_logging_is_idempotent() -> None:
    """Repeated calls must not stack handlers on the root logger."""
    configure_logging("INFO")
    configure_logging("DEBUG")
    configure_logging("WARNING")

    root = logging.getLogger()
    assert len(root.handlers) == 1
    assert root.level == logging.WARNING


def test_get_logger_returns_namespaced_logger() -> None:
    """Loggers are namespaced by module path."""
    logger = get_logger("migmusic.domain.structures")

    assert logger.name == "migmusic.domain.structures"
