"""Health-check router.

The default check returns ``{"status": "ok"}``. A project may override the
check — the callable *and* its response — by setting ``HEALTH_CHECK`` to a
dotted path (``"module.callable"``) that returns a JSON-serializable body,
and/or ``HEALTH_PATH`` to change the route (default ``/health``).
"""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from fastframe.conf import settings

DEFAULT_HEALTH_PATH = "/health"


def _default_health_check() -> dict[str, str]:
    return {"status": "ok"}


def _resolve_health_check() -> Callable[[], Any]:
    """Return the configured health-check callable, or the default.

    ``HEALTH_CHECK`` may be a dotted path (``"module.callable"``) or a
    plain callable. The default returns ``{"status": "ok"}``.
    """
    configured = getattr(settings, "HEALTH_CHECK", None)
    if configured is None:
        return _default_health_check
    if callable(configured):
        return configured
    module_path, _, attr_name = str(configured).rpartition(".")
    if not module_path:
        return _default_health_check
    module = importlib.import_module(module_path)
    return getattr(module, attr_name)


def get_health_router() -> APIRouter:
    """Build and return the health-check router.

    Rebuilt on every call so settings changes (a custom ``HEALTH_CHECK``
    or ``HEALTH_PATH``) take effect when the app factory re-bootstraps.
    """
    path = str(getattr(settings, "HEALTH_PATH", DEFAULT_HEALTH_PATH))
    check = _resolve_health_check()
    router = APIRouter()

    @router.get(path)
    def health_check() -> JSONResponse:
        return JSONResponse(check())

    return router


__all__ = ["get_health_router"]