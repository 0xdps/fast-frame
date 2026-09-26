"""AppConfig for the built-in auth system.

Listing ``"fastframe.contrib.auth"`` in ``INSTALLED_APPS`` is what
registers the built-in ``User``/``Group`` models on ``Model.metadata``
(so migrations pick them up) and mounts the general-purpose
``/api/auth/login``/``/logout``/``/me`` router — not a dedicated
``ENABLE_AUTH_API`` setting. See docs/auth.md.

A project using a custom ``AUTH_USER_MODEL`` (its own app, not
``"auth.User"``) doesn't need this app installed for its *own* model to
work — that model is registered the normal way, via its own app's
``models.py``. Installing this app is specifically for the built-in
``User``/``Group`` models and/or the general-purpose session-auth router.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastframe.core.apps import AppConfig

if TYPE_CHECKING:
    from fastapi import APIRouter


class AuthConfig(AppConfig):
    name = "fastframe.contrib.auth"
    label = "auth"

    def ready(self) -> None:
        from fastframe.conf import settings

        # Only register the built-in User/Group tables when they're
        # actually the active user model — a custom AUTH_USER_MODEL's
        # models are registered by that app's own AppConfig instead.
        if getattr(settings, "AUTH_USER_MODEL", "auth.User") == "auth.User":
            from . import models  # noqa: F401

    def get_routers(self) -> list[APIRouter]:
        from .views import get_auth_router

        return [get_auth_router()]
