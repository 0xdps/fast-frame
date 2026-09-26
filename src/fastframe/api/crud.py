"""The generic REST API's CRUD router — token-authenticated, reuses the
admin registry.

This is a thin wrapper: all the actual list/get/create/update/delete logic
lives in :func:`fastframe.admin.api._build_crud_router`, shared with the
admin API. See :mod:`fastframe.api` for the module-level overview.
"""

from __future__ import annotations

from fastapi import APIRouter

from fastframe.admin.api import _build_crud_router
from fastframe.api.auth import require_token_user


def get_rest_api_router() -> APIRouter:
    """Create the token-authenticated REST API router."""
    try:
        from fastframe.conf import settings

        prefix = str(getattr(settings, "API_PREFIX", "/api/v1"))
        include_in_schema = bool(getattr(settings, "ENABLE_REST_API_DOCS", True))
    except (ImportError, AttributeError):
        prefix = "/api/v1"
        include_in_schema = True

    return _build_crud_router(
        prefix=prefix,
        tags=["rest-api"],
        include_in_schema=include_in_schema,
        auth_dependency=require_token_user,
        source="api",
    )


__all__ = ["get_rest_api_router"]
