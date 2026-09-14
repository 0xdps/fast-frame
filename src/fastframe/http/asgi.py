from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request, Response

from fastframe.core.bootstrap import bootstrap, get_apps_registry
from fastframe.core.settings import load_settings
from fastframe.db.session import begin_session, end_session


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

    app = FastAPI(title=title, debug=debug, **kwargs)
    _include_routers(app, settings_module)
    _add_session_middleware(app, settings_module)
    return app


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
