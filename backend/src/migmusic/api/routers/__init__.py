"""Thin HTTP controllers: no business logic lives here."""

from migmusic.api.routers import health

__all__ = ["health"]
