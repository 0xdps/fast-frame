from __future__ import annotations

import importlib
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from fastframe.core.apps import AppsRegistry
from fastframe.core.bootstrap import bootstrap, get_apps_registry
from fastframe.core.settings import load_settings
from fastframe.db.session import begin_session, end_session
from fastframe.http.discovery import discover_api_routers
from fastframe.models.exceptions import DoesNotExist, MultipleObjectsReturned


def _include_urlconf_routers(app: FastAPI, settings_module: str | None) -> None:
    """Mount a project's own ``routers`` list, from ``ROOT_URLCONF``.

    This is the ``urls.py`` convention (see docs/app-contract.md): a
    project's ``config/urls.py`` aggregates each of its apps' ``router``
    objects into a ``routers = [...]`` list (kept up to date by
    ``manage.py startapp``). It's independent of, and mounted alongside,
    the app-registry routers below.
    """
    settings = load_settings(settings_module)
    root_urlconf = getattr(settings, "ROOT_URLCONF", None)
    if not root_urlconf:
        return

    urls = importlib.import_module(root_urlconf)
    routers = getattr(urls, "routers", None)
    if routers is None and hasattr(urls, "get_routers"):
        routers = urls.get_routers()
    if routers is None:
        return

    for router in routers:
        app.include_router(router)


def _mount_app_registry_routers(app: FastAPI, registry: AppsRegistry) -> None:
    """Mount every installed app's ``AppConfig.get_routers()``, in order.

    This is how batteries — ``fastframe.admin``, ``fastframe.contrib.auth``,
    ``fastframe.api`` — get mounted: purely by being listed in
    ``INSTALLED_APPS``, exactly like adding any other app. Nothing here
    runs, and no battery router is reachable, unless a project opts in by
    installing it. See :meth:`fastframe.core.apps.AppConfig.get_routers`.
    """
    for router in registry.get_routers():
        app.include_router(router)
    for router in discover_api_routers(registry):
        app.include_router(router)


def get_asgi_application(settings_module: str | None = None, **kwargs: Any) -> FastAPI:
    """Return a FastAPI application fully wired up from settings.

    This is FastFrame's one application factory (``create_app()`` is a thin,
    deprecated alias for it). It mounts, in order:

    1. Middleware — ``MIDDLEWARE``, security headers (``SECURE_HEADERS``),
       and CORS (``CORS_ALLOWED_ORIGINS``).
    2. Every installed app's routers (``INSTALLED_APPS`` order) — this is
       what turns on batteries like ``fastframe.admin``,
       ``fastframe.contrib.auth``, and ``fastframe.api``: list them in
       ``INSTALLED_APPS`` and their routers are mounted automatically,
       nothing more required. Leave them out and none of their code runs.
       ``"fastframe.docs"`` is the same kind of switch for Swagger, ReDoc,
       and ``/openapi.json``.
    3. A project's own ``ROOT_URLCONF``-aggregated routers.
    4. The per-request DB session middleware and exception handlers.

    The schema title prefers ``APP_NAME``. Explicit keyword arguments
    always win over that default, including ``docs_url`` if a caller
    builds the app by hand.

    Always re-bootstraps (rebuilding the app registry from the *current*
    settings' ``INSTALLED_APPS``), rather than reusing a previous
    bootstrap — callers that switch settings modules between calls (e.g.
    tests) need each call to reflect the settings actually in effect now,
    since ``INSTALLED_APPS`` membership drives which routers get mounted.
    """
    registry = bootstrap(settings_module)
    settings = registry.settings

    docs_installed = registry.is_installed("fastframe.docs")
    app_kwargs: dict[str, Any] = {
        "title": getattr(settings, "APP_NAME", None) or "FastFrame API",
        "debug": bool(getattr(settings, "DEBUG", False)),
    }
    if docs_installed:
        app_kwargs["openapi_url"] = "/openapi.json"
        app_kwargs["docs_url"] = "/docs"
        app_kwargs["redoc_url"] = "/redoc"
    else:
        app_kwargs["openapi_url"] = None
        app_kwargs["docs_url"] = None
        app_kwargs["redoc_url"] = None

    kwargs.setdefault("lifespan", _make_lifespan())
    app_kwargs.update(kwargs)

    app = FastAPI(**app_kwargs)
    _apply_middleware(app, settings)
    _mount_app_registry_routers(app, registry)
    _include_urlconf_routers(app, settings_module)
    _add_session_middleware(app, settings_module)
    _register_exception_handlers(app)
    return app


def _apply_middleware(app: FastAPI, settings: Any) -> None:
    """Wire up ``MIDDLEWARE`` + the built-in CORS/security-headers middleware.

    Added in this order — ``add_middleware`` makes the *last*-added
    middleware the outermost, so CORS (added last) wraps everything else,
    including error responses from security headers or custom middleware.
    """
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


def _make_lifespan() -> Callable[[FastAPI], Any]:
    """Default lifespan: run every installed app's `shutdown()` hook when
    the ASGI app shuts down. `AppConfig.ready()` already runs synchronously
    during `bootstrap()`, before the app object even exists, so it isn't
    repeated here.

    Only installed when the caller doesn't already pass their own
    `lifespan=` to `get_asgi_application()` — an explicit `lifespan` from
    the caller always wins, and app shutdown hooks won't run automatically
    in that case.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        registry = get_apps_registry()
        for app_config in registry.app_configs:
            hook = getattr(app_config, "shutdown", None)
            if callable(hook):
                hook()

    return lifespan


def _add_session_middleware(app: FastAPI, settings_module: str | None) -> None:
    @app.middleware("http")
    async def db_session_middleware(
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        session, token = begin_session(settings_module)
        try:
            response = await call_next(request)
            end_session(session, token, commit=True)
            return response
        except Exception:
            end_session(session, token, commit=False)
            raise


def _register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DoesNotExist)
    async def handle_does_not_exist(request: Request, exc: DoesNotExist) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(MultipleObjectsReturned)
    async def handle_multiple_objects(
        request: Request, exc: MultipleObjectsReturned
    ) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exc)})
