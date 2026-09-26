"""A minimal set of baseline security response headers.

Not a replacement for a proper security-headers library (no configurable
CSP, no permissions-policy tuning) — just the handful of headers that cost
nothing and have essentially no downside for an API-first framework.
Enabled by default via ``SECURE_HEADERS``; disable per-project if you'd
rather set these yourself (e.g. behind a reverse proxy that already adds
them) or need different values.
"""

from __future__ import annotations

from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds ``X-Content-Type-Options``, ``X-Frame-Options``, and
    ``Referrer-Policy`` to every response. Adds
    ``Strict-Transport-Security`` too, but only when ``DEBUG`` is false —
    HSTS on a plain-HTTP dev server just breaks `localhost` in most browsers.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if not self._debug():
            response.headers.setdefault(
                "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
            )
        return response

    @staticmethod
    def _debug() -> bool:
        try:
            from fastframe.conf import settings

            return bool(getattr(settings, "DEBUG", True))
        except (ImportError, AttributeError):
            return True


__all__ = ["SecurityHeadersMiddleware"]
