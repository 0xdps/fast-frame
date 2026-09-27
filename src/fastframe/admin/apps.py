"""AppConfig for the built-in admin.

Listing ``"fastframe.admin"`` in ``INSTALLED_APPS`` is what turns the
admin on now — not a dedicated ``ENABLE_ADMIN`` setting. Nothing here
runs, and no admin router is mounted, unless a project actually adds this
app, the same way any other app's models/routers are opt-in. See
docs/admin-setup.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastframe.core.apps import AppConfig

if TYPE_CHECKING:
    from fastapi import APIRouter


class AdminConfig(AppConfig):
    name = "fastframe.admin"
    label = "admin"

    def ready(self) -> None:
        # Import side effects only. Three things must be registered before
        # anything creates tables or serves a request:
        #   1. the active user model's admin.py (if any),
        #   2. the audit log model,
        #   3. every installed app's optional admin.py — so that a project's
        #      `admin_site.register(...)` calls (Django-style, module level)
        #      run simply by being in an app named in INSTALLED_APPS. A
        #      missing admin.py is normal and skipped.
        import importlib

        from fastframe.admin import _import_user_admin, ensure_audit_log_registered
        from fastframe.core.bootstrap import get_apps_registry

        _import_user_admin()
        ensure_audit_log_registered()

        for app_config in get_apps_registry().app_configs:
            if not app_config.name:
                continue
            try:
                importlib.import_module(f"{app_config.name}.admin")
            except ModuleNotFoundError:
                continue

    def get_routers(self) -> list[APIRouter]:
        # Auth router first: its literal paths (/login, /logout, /me) must
        # win over the CRUD router's /{resource} catch-all when FastAPI
        # matches routes in registration order.
        from fastframe.admin.api import get_admin_api_router
        from fastframe.admin.auth import get_admin_auth_router
        from fastframe.admin.views import get_admin_router

        return [get_admin_auth_router(), get_admin_api_router(), get_admin_router()]
