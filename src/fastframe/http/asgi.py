from __future__ import annotations

import importlib
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from fastframe.core.bootstrap import bootstrap, get_apps_registry
from fastframe.core.settings import load_settings
from fastframe.db.session import begin_session, end_session
from fastframe.models.exceptions import DoesNotExist, MultipleObjectsReturned


def _include_routers(app: FastAPI, settings_module: str | None) -> None:
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


def get_asgi_application(settings_module: str | None = None, **kwargs: Any) -> FastAPI:
    """Return a FastAPI application with installed app routers mounted."""
    bootstrap(settings_module)
    settings = get_apps_registry().settings
    title = getattr(settings, "APP_NAME", "FastFrame")
    debug = getattr(settings, "DEBUG", False)

    kwargs.setdefault("lifespan", _make_lifespan())

    app = FastAPI(title=title, debug=debug, **kwargs)
    _include_routers(app, settings_module)
    _add_session_middleware(app, settings_module)
    _register_exception_handlers(app)
    return app


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
