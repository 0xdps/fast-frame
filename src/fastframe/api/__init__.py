"""FastFrame generic REST API — token-authenticated CRUD.

An opt-in alternative to the cookie-session admin API, for non-browser
clients: mobile apps, scripts, third-party integrations. It exposes the
*same* models registered with ``admin_site`` (see
:mod:`fastframe.admin.site`) — anything visible in the admin is reachable
here too, just authenticated with a bearer token instead of a session
cookie, and open to any active user rather than only ``can_access_admin``
users.

Usage:
    # settings.py
    INSTALLED_APPS = [..., "fastframe.api"]

    # app.py (only needed if not going through
    # get_asgi_application()/create_app(), which do this automatically
    # for installed apps — see fastframe.api.apps.RestApiConfig)
    from fastframe.api import include_rest_api
    include_rest_api(app)

Obtain a token:
    POST /api/auth/token  {"username": "...", "password": "..."}
    -> {"data": {"token": "..."}}   # shown once — store it now

Use it:
    GET /api/v1/{resource}
    Authorization: Bearer <token>

Revoke it:
    DELETE /api/auth/token
    Authorization: Bearer <token>
"""

from __future__ import annotations

from typing import Any

from fastframe.api.auth import get_rest_auth_router, require_token_user
from fastframe.api.crud import get_rest_api_router

__all__ = [
    "get_rest_api_router",
    "get_rest_auth_router",
    "require_token_user",
    "include_rest_api",
]


def include_rest_api(app: Any) -> None:
    """Mount the REST auth + CRUD routers onto ``app``, unconditionally.

    For manual wiring when a project builds its own ``FastAPI()`` instead
    of going through ``get_asgi_application()``/``create_app()``. Calling
    this *is* the opt-in — projects using ``INSTALLED_APPS`` should add
    ``"fastframe.api"`` instead of calling this directly (see
    :class:`fastframe.api.apps.RestApiConfig`).
    """
    import importlib

    from fastframe.admin import ensure_audit_log_registered

    ensure_audit_log_registered()
    importlib.import_module("fastframe.contrib.auth.tokens")  # register the Token model
    app.include_router(get_rest_auth_router())
    app.include_router(get_rest_api_router())
