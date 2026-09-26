"""FastFrame generic REST API — token-authenticated CRUD.

An opt-in (``ENABLE_REST_API``) alternative to the cookie-session admin API,
for non-browser clients: mobile apps, scripts, third-party integrations.
It exposes the *same* models registered with ``admin_site`` (see
:mod:`fastframe.admin.site`) — anything visible in the admin is reachable
here too, just authenticated with a bearer token instead of a session
cookie, and open to any active user rather than only ``can_access_admin``
users.

Usage:
    # settings.py
    ENABLE_REST_API = True

    # app.py
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
    """Mount the REST auth + CRUD routers when ``ENABLE_REST_API`` is true.

    Off by default (unlike admin) — this is a new, additional way to reach
    whatever models are already registered with ``admin_site``, so it's
    opt-in rather than mounted automatically.
    """
    import importlib

    from fastframe.admin import ensure_audit_log_registered
    from fastframe.conf import settings

    if not getattr(settings, "ENABLE_REST_API", False):
        return
    ensure_audit_log_registered()
    importlib.import_module("fastframe.contrib.auth.tokens")  # register the Token model
    app.include_router(get_rest_auth_router())
    app.include_router(get_rest_api_router())
