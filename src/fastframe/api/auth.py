"""Bearer-token authentication for the generic REST API.

Any active user with a valid token may use the REST API — unlike admin,
which additionally requires ``can_access_admin``. Per-model permissions
still apply via each model's ``ModelAdmin`` (``has_add_permission``, etc.),
since both surfaces share the same registry.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from fastframe.contrib.auth.dependencies import snapshot_user as _snapshot_user


def require_token_user(request: Request) -> Any:
    """FastAPI dependency: enforce bearer-token authentication.

    Raises:
        HTTPException(401): Missing/invalid/unknown token.
        HTTPException(403): Token is valid, but the user is inactive.
    """
    auth_header = request.headers.get("authorization", "")
    scheme, _, raw_token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not raw_token:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    from fastframe.contrib.auth.tokens import get_user_from_token
    from fastframe.db.session import session_scope

    with session_scope():
        user = get_user_from_token(raw_token.strip())
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        if not getattr(user, "is_active", True):
            raise HTTPException(status_code=403, detail="User is inactive")
        return _snapshot_user(user)


def get_rest_auth_router() -> APIRouter:
    """Create the token obtain/revoke router."""
    try:
        from fastframe.conf import settings

        enable_docs = bool(getattr(settings, "ENABLE_REST_API_DOCS", True))
    except (ImportError, AttributeError):
        enable_docs = True

    router = APIRouter(prefix="/api/auth", tags=["rest-auth"], include_in_schema=enable_docs)

    @router.post("/token", status_code=201)
    async def obtain_token(request: Request) -> dict[str, Any]:
        """Exchange username/password for a new API token (shown once).

        Optional body fields: ``name`` (label) and ``expiresInDays`` (int,
        or ``null`` for a token that never expires — the default unless
        ``API_TOKEN_DEFAULT_EXPIRY_DAYS`` is set).
        """
        from fastframe.contrib.auth import authenticate
        from fastframe.contrib.auth.tokens import create_token
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
        name = str(body.get("name", ""))

        enforce_login_rate_limit(request, username or "unknown")

        token_kwargs: dict[str, Any] = {}
        if "expiresInDays" in body:
            token_kwargs["expires_in_days"] = body["expiresInDays"]

        with session_scope():
            user = authenticate(username, password)
            if user is None:
                raise HTTPException(status_code=401, detail="Invalid username or password")
            raw_token = create_token(user, name=name, **token_kwargs)

        record_login_success(request, username)
        return {"data": {"token": raw_token}}

    @router.delete("/token")
    async def revoke_current_token(request: Request) -> dict[str, Any]:
        """Revoke the token used to authenticate this request."""
        from fastframe.contrib.auth.tokens import revoke_token
        from fastframe.db.session import session_scope

        auth_header = request.headers.get("authorization", "")
        scheme, _, raw_token = auth_header.partition(" ")
        if scheme.lower() != "bearer" or not raw_token:
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

        with session_scope():
            found = revoke_token(raw_token.strip())
        if not found:
            raise HTTPException(status_code=404, detail="Token not found")
        return {"data": {"revoked": True}}

    return router


__all__ = ["require_token_user", "get_rest_auth_router"]
