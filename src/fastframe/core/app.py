"""FastAPI application factory that honors FastFrame settings."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI


def create_app(*, include_admin: bool | None = None, **kwargs: Any) -> FastAPI:
    """Create a FastAPI app configured from settings.

    OpenAPI/Swagger follows ``ENABLE_OPENAPI``, ``OPENAPI_URL``,
    ``SWAGGER_UI_URL``, and ``REDOC_URL``. Admin routes are mounted when
    ``ENABLE_ADMIN`` is true, unless ``include_admin`` overrides that.

    Explicit keyword arguments win over settings (``title``, ``docs_url``,
    and any other ``FastAPI`` argument).
    """
    from fastframe.conf import settings
    from fastframe.core.bootstrap import bootstrap, get_apps_registry

    try:
        get_apps_registry()
    except RuntimeError:
        bootstrap()
    else:
        settings.reload()

    enable_openapi = bool(getattr(settings, "ENABLE_OPENAPI", True))
    app_kwargs: dict[str, Any] = {
        "title": getattr(settings, "OPENAPI_TITLE", "FastFrame API"),
        "version": getattr(settings, "OPENAPI_VERSION", "1.0.0"),
        "description": getattr(settings, "OPENAPI_DESCRIPTION", "API Documentation"),
    }
    if enable_openapi:
        app_kwargs["openapi_url"] = getattr(settings, "OPENAPI_URL", "/openapi.json")
        app_kwargs["docs_url"] = getattr(settings, "SWAGGER_UI_URL", "/docs")
        app_kwargs["redoc_url"] = getattr(settings, "REDOC_URL", "/redoc")
    else:
        app_kwargs["openapi_url"] = None
        app_kwargs["docs_url"] = None
        app_kwargs["redoc_url"] = None

    app_kwargs.update(kwargs)
    app = FastAPI(**app_kwargs)

    if include_admin is None:
        mount_admin = bool(getattr(settings, "ENABLE_ADMIN", True))
    else:
        mount_admin = include_admin
    if mount_admin:
        from fastframe.admin import include_admin as mount

        mount(app)
    return app
