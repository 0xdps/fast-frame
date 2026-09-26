"""Admin authentication — session-cookie login for the admin API and UI.

Adds Django-like ``login_required`` protection to the admin:

* ``POST /api/admin/login``  — verify credentials, set a signed session cookie
* ``POST /api/admin/logout`` — clear the session cookie
* ``GET  /api/admin/me``     — return the current admin user (or 401)

All other admin API routes require a valid session belonging to a user with
``can_access_admin`` (see :mod:`fastframe.contrib.auth.models`). Set
``ADMIN_REQUIRE_AUTH = False`` in settings to disable this (development only
— see ``docs/ADMIN_SECURITY_WARNING.md``).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

SESSION_COOKIE_NAME = "ff_admin_session"


def _admin_auth_settings() -> tuple[bool, bool]:
    """Return (require_auth, debug) from settings, with safe defaults."""
    try:
        from fastframe.conf import settings

        return (
            bool(getattr(settings, "ADMIN_REQUIRE_AUTH", True)),
            bool(getattr(settings, "DEBUG", True)),
        )
    except (ImportError, AttributeError):
        return True, True


def _snapshot_user(user: Any) -> Any:
    """Copy the fields we need off a user into a plain, session-free object.

    The lookup session is closed (and commits, expiring attributes) before
    callers get a chance to read from ``user``, so we take a snapshot while
    it's still attached rather than returning the ORM instance itself.
    """
    import types

    from fastframe.admin.serializers import get_pk_name

    pk_name = get_pk_name(type(user))
    return types.SimpleNamespace(
        id=getattr(user, pk_name, None),
        username=getattr(user, "username", None),
        email=getattr(user, "email", None),
        is_active=bool(getattr(user, "is_active", True)),
        is_superuser=bool(getattr(user, "is_superuser", False)),
        can_access_admin=bool(getattr(user, "can_access_admin", False)),
    )


def get_current_admin_user(request: Request) -> Any | None:
    """Return the authenticated admin user for this request, or ``None``.

    Returns a lightweight snapshot (not a live ORM instance) — see
    :func:`_snapshot_user`. Does not raise — use :func:`require_admin_user`
    as a route dependency when authentication should be enforced.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    from fastframe.contrib.auth.session import verify_session_token

    data = verify_session_token(token)
    if not data or "user_id" not in data:
        return None

    from fastframe.admin.serializers import get_pk_name
    from fastframe.contrib.auth import get_user_model
    from fastframe.db.session import session_scope

    user_model = get_user_model()
    pk_name = get_pk_name(user_model)
    try:
        # Dependency resolution runs before the route body binds a request
        # session (see fastframe.admin.api._admin_session), so open our own.
        with session_scope():
            user = user_model.objects.get(**{pk_name: data["user_id"]})
            if not getattr(user, "is_active", True):
                return None
            return _snapshot_user(user)
    except Exception:  # noqa: BLE001 - any lookup failure => no session user
        return None


def require_admin_user(request: Request) -> Any:
    """FastAPI dependency: enforce admin authentication + authorization.

    Raises:
        HTTPException(401): No valid session (not logged in).
        HTTPException(403): Logged in, but lacks ``can_access_admin``.
    """
    require_auth, _ = _admin_auth_settings()
    if not require_auth:
        return None

    user = get_current_admin_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not getattr(user, "can_access_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def _user_summary(user: Any) -> dict[str, Any]:
    """Build the JSON-safe response body for a user snapshot (see _snapshot_user)."""
    from fastframe.admin.serializers import serialize_value

    return {
        "id": serialize_value(getattr(user, "id", None)),
        "username": getattr(user, "username", None),
        "email": getattr(user, "email", None),
        "isSuperuser": bool(getattr(user, "is_superuser", False)),
        "canAccessAdmin": bool(getattr(user, "can_access_admin", False)),
    }


def _set_session_cookie(response: Response, user_id: Any) -> None:
    from fastframe.admin.serializers import serialize_value
    from fastframe.contrib.auth.session import DEFAULT_MAX_AGE, create_session_token

    _, debug = _admin_auth_settings()
    token = create_session_token({"user_id": serialize_value(user_id)})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=DEFAULT_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=not debug,
        path="/",
    )


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
        from fastframe.db.session import session_scope

        try:
            body = await request.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from e
        if not isinstance(body, dict):
            raise HTTPException(status_code=400, detail="JSON body must be an object")

        username = str(body.get("username", ""))
        password = str(body.get("password", ""))
        with session_scope():
            user = authenticate(username, password)
            if user is None:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            if not getattr(user, "can_access_admin", False):
                raise HTTPException(status_code=403, detail="Admin access required")
            snapshot = _snapshot_user(user)

        _set_session_cookie(response, snapshot.id)
        return {"data": _user_summary(snapshot)}

    @router.post("/logout")
    async def logout(response: Response) -> dict[str, Any]:
        """Clear the admin session cookie."""
        response.delete_cookie(SESSION_COOKIE_NAME, path="/")
        return {"data": {"loggedOut": True}}

    @router.get("/me")
    async def me(request: Request) -> dict[str, Any]:
        """Return the current admin user, or 401 if not logged in."""
        user = get_current_admin_user(request)
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
