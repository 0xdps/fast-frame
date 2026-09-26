"""FastFrame Admin - Django-like admin interface.

Provides automatic CRUD interface for your models with:
- List views with search, filters, and pagination
- Create/Edit forms with validation
- Delete confirmations
- Performance optimizations (auto select_related, limits)
- SSR-first with htmx for progressive enhancement

Usage:
    # In your app's admin.py
    from fastframe.admin import ModelAdmin, admin_site
    from myapp.models import Post

    class PostAdmin(ModelAdmin):
        list_display = ["title", "author", "status", "created_at"]
        search_fields = ["title", "content"]
        list_filter = ["status", "category"]
        list_per_page = 50

    admin_site.register(Post, PostAdmin)

    # In your main app
    from fastframe.admin import get_admin_router
    app.include_router(get_admin_router())

Then visit http://localhost:8000/admin/
"""

from __future__ import annotations

from typing import Any

from fastframe.admin.api import get_admin_api_router
from fastframe.admin.auth import get_admin_auth_router
from fastframe.admin.site import AdminSite, ModelAdmin, admin_site
from fastframe.admin.views import get_admin_router

__all__ = [
    "AdminSite",
    "ModelAdmin",
    "admin_site",
    "get_admin_router",
    "get_admin_api_router",
    "get_admin_auth_router",
    "include_admin",
]


def _import_user_admin() -> None:
    """Import the active user model's admin module so it is registered."""
    import importlib

    from fastframe.conf import settings

    model_path = getattr(settings, "AUTH_USER_MODEL", "auth.User")
    app_label = model_path.split(".", 1)[0]
    if app_label == "auth":
        importlib.import_module("fastframe.contrib.auth.admin")
        return
    importlib.import_module(f"{app_label}.models")
    try:
        importlib.import_module(f"{app_label}.admin")
    except ImportError:
        return


def include_admin(app: Any) -> None:
    """Mount the admin API and UI when ``ENABLE_ADMIN`` is true.

    Does nothing when admin is disabled, so OpenAPI stays free of admin routes.

    The auth router (login/logout/me) is mounted *before* the CRUD router so
    its literal paths (``/login``, ``/logout``, ``/me``) win over the CRUD
    router's ``/{resource}`` catch-all when FastAPI matches routes in
    registration order.
    """
    from fastframe.conf import settings

    if not getattr(settings, "ENABLE_ADMIN", True):
        return
    _import_user_admin()
    app.include_router(get_admin_auth_router())
    app.include_router(get_admin_api_router())
    app.include_router(get_admin_router())
