"""Tests for the lazy application entry point in ``migmusic.main``."""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from migmusic import main


def test_app_attribute_is_built_on_demand() -> None:
    """``uvicorn migmusic.main:app`` resolves the ASGI object lazily."""
    app = main.__getattr__("app")

    assert isinstance(app, FastAPI)
    assert app.state.settings.app_env == "development"


def test_unknown_attribute_still_raises_attribute_error() -> None:
    """The PEP 562 hook must not swallow unrelated attribute lookups."""
    with pytest.raises(AttributeError, match="has no attribute"):
        main.__getattr__("something_else")
