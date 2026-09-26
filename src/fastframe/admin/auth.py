"""Admin authentication — session-cookie login for the admin API and UI.

Adds Django-like ``login_required`` protection to the admin:

* ``POST /api/admin/login``  — verify credentials, set a signed session cookie
* ``POST /api/admin/logout`` — clear the session cookie
* ``GET  /api/admin/me``     — return the current admin user (or 401)

All other admin API routes require a valid session belonging to a user with
``can_access_admin`` (see :mod:`fastframe.contrib.auth.models`). This is not
optional — there is no setting to disable it (see
``docs/ADMIN_SECURITY_WARNING.md``).

This is the admin-specific layer on top of
:mod:`fastframe.contrib.auth.dependencies`'s general session mechanism: the
same cookie set here is also honored by ``login_required``/
``get_current_user`` on any other app route, and a session started via the
general ``/api/auth/login`` also lets a ``can_access_admin`` user straight
into the admin without logging in twice.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from fastframe.contrib.auth.dependencies import (
    SESSION_COOKIE_NAME,
    clear_session_cookie,
    get_current_user,
    set_session_cookie,
)


def get_current_admin_user(request: Request) -> Any | None:
    """Return the authenticated user for this request, or ``None``.

    Just :func:`fastframe.contrib.auth.dependencies.get_current_user` under
    a name that predates that module — kept so existing imports of
    ``fastframe.admin.auth.get_current_admin_user`` keep working. Does
    *not* check ``can_access_admin`` — use :func:`require_admin_user` as a
    route dependency when authorization should be enforced too.
    """
    return get_current_user(request)


def require_admin_user(request: Request) -> Any:
    """FastAPI dependency: enforce admin authentication + authorization.

    Always enforced — admin has no "no auth" mode.

    Raises:
        HTTPException(401): No valid session (not logged in).
        HTTPException(403): Logged in, but lacks ``can_access_admin``.
    """
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not getattr(user, "can_access_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _user_summary(user: Any) -> dict[str, Any]:
    """Build the JSON-safe response body for a user snapshot (see snapshot_user)."""
    from fastframe.admin.serializers import serialize_value

    return {
        "id": serialize_value(getattr(user, "id", None)),
        "username": getattr(user, "username", None),
        "email": getattr(user, "email", None),
        "isSuperuser": bool(getattr(user, "is_superuser", False)),
        "canAccessAdmin": bool(getattr(user, "can_access_admin", False)),
    }


def get_admin_auth_router() -> APIRouter:
    """Create the login/logout/me router, mounted under the admin API prefix."""
    try:
        from fastframe.conf import settings

        admin_api_prefix = str(getattr(settings, "ADMIN_API_PREFIX", "/api/admin"))
        enable_admin_docs = bool(getattr(settings, "ENABLE_ADMIN_DOCS", True))
    except (ImportError, AttributeError):
        admin_api_prefix = "/api/admin"
        enable_admin_docs = True

    router = APIRouter(
        prefix=admin_api_prefix,
        tags=["admin-auth"],
        include_in_schema=enable_admin_docs,
    )

    @router.post("/login")
    async def login(request: Request, response: Response) -> dict[str, Any]:
        """Verify credentials and set the admin session cookie."""
        from fastframe.contrib.auth import authenticate
        from fastframe.contrib.auth.dependencies import snapshot_user
        from fastframe.core.ratelimit import enforce_login_rate_limit, record_login_success
        from fastframe.db.session import session_scope

        try:
            body = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from e
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="JSON body must be an object")

        username = str(body.get("username", ""))
        password = str(body.get("password", ""))

        enforce_login_rate_limit(request, username or "unknown")

        with session_scope():
            user = authenticate(username, password)
            if user is None:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            if not getattr(user, "can_access_admin", False):
                raise HTTPException(status_code=403, detail="Admin access required")
            snapshot = snapshot_user(user)
            session_version = user.session_version

        record_login_success(request, username)
        set_session_cookie(response, user_id=snapshot.id, session_version=session_version)
        return {"data": _user_summary(snapshot)}

    @router.post("/logout")
    async def logout(response: Response) -> dict[str, Any]:
        """Clear the admin session cookie."""
        clear_session_cookie(response)
        return {"data": {"loggedOut": True}}

    @router.get("/me")
    async def me(request: Request) -> dict[str, Any]:
        """Return the current admin user, or 401 if not logged in."""
        user = get_current_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {"data": _user_summary(user)}

    return router


__all__ = [
    "SESSION_COOKIE_NAME",
    "get_current_admin_user",
    "require_admin_user",
    "get_admin_auth_router",
]
