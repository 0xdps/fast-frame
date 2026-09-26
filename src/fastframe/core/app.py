"""Deprecated alias for :func:`fastframe.http.asgi.get_asgi_application`.

``create_app()`` predates the unification of FastFrame's two application
factories. ``get_asgi_application()`` now does everything this used to do
(app-registry router mounting, ``MIDDLEWARE``/CORS/security headers) *plus*
what it always did (``ROOT_URLCONF`` routers, DB session middleware) — use
it directly in new code. This wrapper only exists so existing
``config/asgi.py``/``app.py`` files that call ``create_app()`` keep working.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI


def create_app(**kwargs: Any) -> FastAPI:
    """Deprecated: use :func:`fastframe.http.asgi.get_asgi_application` instead.

    Batteries (``fastframe.admin``, ``fastframe.contrib.auth``,
    ``fastframe.api``) are mounted when listed in ``INSTALLED_APPS`` — not
    via an ``include_admin`` override or ``ENABLE_*`` settings, both of
    which this function no longer accepts/reads.
    """
    from fastframe.http.asgi import get_asgi_application

    return get_asgi_application(**kwargs)
