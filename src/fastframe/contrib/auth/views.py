"""General-purpose session login — ``/api/auth/login``, ``/logout``, ``/me``.

Unlike ``/api/admin/login`` (:mod:`fastframe.admin.auth`), this doesn't
check ``can_access_admin`` — any active user can start a session here. It's
the same cookie either way (:mod:`fastframe.contrib.auth.dependencies`), so
a session started here also works for the admin if the user happens to
have admin access, and vice versa.

Intended for app code that wants cookie-session auth on its own routes
without going through the admin at all — see
:func:`fastframe.contrib.auth.dependencies.login_required` and
:func:`~fastframe.contrib.auth.dependencies.permission_required`.

Mounted automatically by ``get_asgi_application()``/``create_app()`` when
``"fastframe.contrib.auth"`` is in ``INSTALLED_APPS`` — see
:class:`fastframe.contrib.auth.apps.AuthConfig`.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from .dependencies import (
    clear_session_cookie,
    get_current_user,
    set_session_cookie,
    snapshot_user,
)


def _user_summary(user: Any) -> dict[str, Any]:
    from fastframe.admin.serializers import serialize_value

    return {
        "id": serialize_value(getattr(user, "id", None)),
        "username": getattr(user, "username", None),
        "email": getattr(user, "email", None),
        "isSuperuser": bool(getattr(user, "is_superuser", False)),
        "canAccessAdmin": bool(getattr(user, "can_access_admin", False)),
        "permissions": sorted(getattr(user, "permissions", None) or []),
    }


def get_auth_router() -> APIRouter:
    """Create the general login/logout/me router."""
    try:
        from fastframe.conf import settings

        enable_docs = bool(getattr(settings, "ENABLE_REST_API_DOCS", True))
    except (ImportError, AttributeError):
        enable_docs = True

    router = APIRouter(prefix="/api/auth", tags=["auth"], include_in_schema=enable_docs)

    @router.post("/login")
    async def login(request: Request, response: Response) -> dict[str, Any]:
        """Verify credentials and set the shared session cookie."""
        from fastframe.contrib.auth import authenticate
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
            snapshot = snapshot_user(user)
            session_version = user.session_version

        record_login_success(request, username)
        set_session_cookie(response, user_id=snapshot.id, session_version=session_version)
        return {"data": _user_summary(snapshot)}

    @router.post("/logout")
    async def logout(response: Response) -> dict[str, Any]:
        """Clear the session cookie."""
        clear_session_cookie(response)
        return {"data": {"loggedOut": True}}

    @router.get("/me")
    async def me(request: Request) -> dict[str, Any]:
        """Return the current user, or 401 if not logged in."""
        user = get_current_user(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {"data": _user_summary(user)}

    return router


__all__ = ["get_auth_router"]
