"""Framework-level dependencies (FastAPI ``Depends`` providers).

Services are constructed here, never inside routers, so the composition stays
in one place and tests can override a single provider.
"""

from __future__ import annotations

from typing import Annotated, cast

from fastapi import Request

from migmusic.core import Settings


def get_app_settings(request: Request) -> Settings:
    """Return the settings instance attached by the composition root."""
    return cast(Settings, request.app.state.settings)


SettingsDep = Annotated[Settings, "Provides typed access to application settings."]
