"""Tests for the base exception hierarchy."""

from __future__ import annotations

from migmusic.core import (
    ConfigurationError,
    DomainError,
    ExternalServiceError,
    MigMusicError,
    NotFoundError,
    ValidationError,
)


def test_every_error_derives_from_migmusic_error() -> None:
    """A single root exception lets callers catch all application errors."""
    for error_cls in (
        ConfigurationError,
        DomainError,
        NotFoundError,
        ValidationError,
        ExternalServiceError,
    ):
        assert issubclass(error_cls, MigMusicError)


def test_domain_errors_form_a_hierarchy() -> None:
    """Handlers can map the whole domain layer in one place."""
    assert issubclass(NotFoundError, DomainError)
    assert issubclass(ValidationError, DomainError)


def test_external_service_error_carries_service_and_status() -> None:
    """Upstream failures keep the failing service and its HTTP status."""
    exc = ExternalServiceError("boom", service="spotify", status_code=503)

    assert exc.service == "spotify"
    assert exc.status_code == 503
    assert str(exc) == "boom"


def test_external_service_error_defaults_to_unknown_status() -> None:
    """A missing status is represented as ``None`` rather than a guess."""
    exc = ExternalServiceError("boom", service="postgres")

    assert exc.status_code is None
