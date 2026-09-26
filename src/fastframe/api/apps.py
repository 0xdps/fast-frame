"""AppConfig for the generic, token-authenticated REST API.

Listing ``"fastframe.api"`` in ``INSTALLED_APPS`` is what turns this on
now — not a dedicated ``ENABLE_REST_API`` setting. See docs/rest-api.md.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastframe.core.apps import AppConfig

if TYPE_CHECKING:
    from fastapi import APIRouter


class RestApiConfig(AppConfig):
    name = "fastframe.api"
    label = "api"

    def ready(self) -> None:
        import importlib

        from fastframe.admin import ensure_audit_log_registered

        ensure_audit_log_registered()
        importlib.import_module("fastframe.contrib.auth.tokens")  # register Token

    def get_routers(self) -> list[APIRouter]:
        from fastframe.api.auth import get_rest_auth_router
        from fastframe.api.crud import get_rest_api_router

        return [get_rest_auth_router(), get_rest_api_router()]
