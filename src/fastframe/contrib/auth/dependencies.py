"""General-purpose, session-cookie-based auth for *any* FastAPI route.

This is the shared engine behind both the admin's login/logout/me
(:mod:`fastframe.admin.auth`, which additionally requires
``can_access_admin``) and the plain ``/api/auth/login`` endpoints
(:mod:`fastframe.contrib.auth.views`) — same signed cookie, same user
lookup, same session-revocation check. App code can depend on
:func:`get_current_user`, :func:`login_required`, or
:func:`permission_required` directly in its own routers, without going
through admin at all::

    from fastframe.contrib.auth.dependencies import login_required

    @router.get("/my-profile")
    def my_profile(user: Any = Depends(login_required)):
        return {"username": user.username}
"""

from __future__ import annotations

import types
from typing import Any

from fastapi import HTTPException, Request, Response

# Same cookie for the admin ("/api/admin/login", additionally gated on
# can_access_admin) and general-purpose ("/api/auth/login") logins — one
# session serves both surfaces. Name kept as-is for backward compatibility
# (predates this module; used to live in fastframe.admin.auth).
SESSION_COOKIE_NAME = "ff_admin_session"


def _debug_setting() -> bool:
    try:
        from fastframe.conf import settings

        return bool(getattr(settings, "DEBUG", True))
    except (ImportError, AttributeError):
        return True


def snapshot_user(user: Any) -> Any:
    """Copy the fields we need off a live user into a session-free snapshot.

    Includes the *flattened* effective permission set (own + every group's)
    computed now, while ``user`` is still attached to a session — the
    snapshot itself has no ``.groups`` relationship to walk later.
    """
    from fastframe.admin.serializers import get_pk_name

    from .permissions import get_effective_permissions

    pk_name = get_pk_name(type(user))
    return types.SimpleNamespace(
        id=getattr(user, pk_name, None),
        username=getattr(user, "username", None),
        email=getattr(user, "email", None),
        is_active=bool(getattr(user, "is_active", True)),
        is_superuser=bool(getattr(user, "is_superuser", False)),
        can_access_admin=bool(getattr(user, "can_access_admin", False)),
        permissions=get_effective_permissions(user),
    )


def get_current_user(request: Request) -> Any | None:
    """Return the authenticated user for this request, or ``None``.

    Verifies the signed session cookie (signature, expiry, and that its
    embedded session version still matches the user's current
    ``session_version`` — see ``User.invalidate_sessions()``), then loads
    and snapshots the user. Never raises — use :func:`login_required` or
    :func:`permission_required` as a route dependency to enforce auth.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    from .session import verify_session_token

    data = verify_session_token(token)
    if not data or "user_id" not in data:
        return None

    from fastframe.admin.serializers import get_pk_name
    from fastframe.db.session import session_scope

    from . import get_user_model

    user_model = get_user_model()
    pk_name = get_pk_name(user_model)
    try:
        with session_scope():
            user = user_model.objects.get(**{pk_name: data["user_id"]})
            if not getattr(user, "is_active", True):
                return None
            if int(data.get("sv", 0)) != int(getattr(user, "session_version", 0)):
                return None  # session was invalidated after this cookie was issued
            return snapshot_user(user)
    except Exception:  # noqa: BLE001 - any lookup failure => no session user
        return None


def login_required(request: Request) -> Any:
    """FastAPI dependency: require *any* active, logged-in user.

    Unlike :func:`fastframe.admin.auth.require_admin_user`, this does not
    check ``can_access_admin`` — any active user with a valid session
    cookie passes.

    Raises:
        HTTPException(401): No valid session.
    """
    user = get_current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def permission_required(perm: str):
    """Build a FastAPI dependency requiring ``login_required`` plus ``perm``.

    Args:
        perm: A permission string, e.g. ``"blog.change_post"`` (see
            :mod:`fastframe.contrib.auth.permissions`). Superusers always
            pass regardless of ``perm``.

    Example:
        @router.post("/posts/{id}/publish")
        def publish(id: int, user=Depends(permission_required("blog.change_post"))):
            ...
    """

    def dependency(request: Request) -> Any:
        from .permissions import user_has_perm

        user = login_required(request)
        if not user_has_perm(user, perm):
            raise HTTPException(status_code=403, detail=f"Missing permission: {perm}")
        return user

    return dependency


def set_session_cookie(response: Response, *, user_id: Any, session_version: int) -> None:
    """Set the shared session cookie for ``user_id``."""
    from fastframe.admin.serializers import serialize_value

    from .session import DEFAULT_MAX_AGE, create_session_token

    token = create_session_token(
        {"user_id": serialize_value(user_id), "sv": int(session_version)}
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=DEFAULT_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=not _debug_setting(),
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    """Clear the shared session cookie."""
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


__all__ = [
    "SESSION_COOKIE_NAME",
    "snapshot_user",
    "get_current_user",
    "login_required",
    "permission_required",
    "set_session_cookie",
    "clear_session_cookie",
]
