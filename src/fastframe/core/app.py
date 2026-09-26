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

    _apply_middleware(app, settings)

    if bool(getattr(settings, "ENABLE_AUTH_API", True)):
        from fastframe.contrib.auth.views import get_auth_router

        app.include_router(get_auth_router())

    if include_admin is None:
        mount_admin = bool(getattr(settings, "ENABLE_ADMIN", True))
    else:
        mount_admin = include_admin
    if mount_admin:
        from fastframe.admin import include_admin as mount

        mount(app)

    if bool(getattr(settings, "ENABLE_REST_API", False)):
        from fastframe.api import include_rest_api

        include_rest_api(app)
    return app


def _apply_middleware(app: FastAPI, settings: Any) -> None:
    """Wire up ``MIDDLEWARE`` + the built-in CORS/security-headers middleware.

    Added in this order — ``add_middleware`` makes the *last*-added
    middleware the outermost, so CORS (added last) wraps everything else,
    including error responses from security headers or custom middleware.
    """
    import importlib

    for dotted_path in getattr(settings, "MIDDLEWARE", None) or []:
        module_path, _, class_name = str(dotted_path).rpartition(".")
        if not module_path:
            raise ImportError(
                f"Invalid MIDDLEWARE entry (expected 'module.ClassName'): {dotted_path!r}"
            )
        middleware_cls = getattr(importlib.import_module(module_path), class_name)
        app.add_middleware(middleware_cls)

    if bool(getattr(settings, "SECURE_HEADERS", True)):
        from fastframe.middleware.security import SecurityHeadersMiddleware

        app.add_middleware(SecurityHeadersMiddleware)

    cors_origins = getattr(settings, "CORS_ALLOWED_ORIGINS", None) or []
    if cors_origins:
        from starlette.middleware.cors import CORSMiddleware

        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(cors_origins),
            allow_credentials=bool(getattr(settings, "CORS_ALLOW_CREDENTIALS", False)),
            allow_methods=list(getattr(settings, "CORS_ALLOW_METHODS", None) or ["*"]),
            allow_headers=list(getattr(settings, "CORS_ALLOW_HEADERS", None) or ["*"]),
        )
