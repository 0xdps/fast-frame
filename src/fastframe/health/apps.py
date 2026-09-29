"""AppConfig for the built-in health check.

Listing ``"fastframe.health"`` in ``INSTALLED_APPS`` is what turns the
``/health`` endpoint on — not a dedicated ``ENABLE_HEALTH`` setting. The
check itself (function and response) is overridable via ``HEALTH_CHECK``,
and the route path via ``HEALTH_PATH``. See docs/settings.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastframe.core.apps import AppConfig

if TYPE_CHECKING:
    from fastapi import APIRouter


class HealthConfig(AppConfig):
    name = "fastframe.health"
    label = "health"

    def get_routers(self) -> list[APIRouter]:
        from fastframe.health.views import get_health_router

        return [get_health_router()]
