"""Tests for create_app()'s built-in CORS/security-headers middleware and
the MIDDLEWARE setting (fastframe.core.app._apply_middleware).
"""


import pytest
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from fastframe.core.app import create_app


class _MarkerMiddleware(BaseHTTPMiddleware):
    """A trivial custom middleware, for testing the MIDDLEWARE setting."""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Marker"] = "hit"
        return response


@pytest.fixture
def _settings_module(monkeypatch, tmp_path):
    monkeypatch.setenv("FASTFRAME_SETTINGS_MODULE", "tests.fixtures.test_settings")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'middleware.db'}")
    return "tests.fixtures.test_settings"


def test_security_headers_present_by_default(_settings_module):
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.headers.get("x-content-type-options") == "nosniff"
    assert resp.headers.get("x-frame-options") == "DENY"
    assert resp.headers.get("referrer-policy") == "same-origin"


def test_hsts_absent_in_debug_mode(_settings_module, monkeypatch):
    monkeypatch.setattr("tests.fixtures.test_settings.DEBUG", True)
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert "strict-transport-security" not in {k.lower() for k in resp.headers}


def test_hsts_present_when_not_debug(_settings_module, monkeypatch):
    monkeypatch.setattr("tests.fixtures.test_settings.DEBUG", False)
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert "max-age" in resp.headers.get("strict-transport-security", "")


def test_security_headers_can_be_disabled(_settings_module, monkeypatch):
    monkeypatch.setattr("tests.fixtures.test_settings.SECURE_HEADERS", False, raising=False)
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert "x-frame-options" not in {k.lower() for k in resp.headers}


def test_cors_disabled_by_default(_settings_module):
    app = create_app()
    with TestClient(app) as client:
        resp = client.get(
            "/openapi.json", headers={"Origin": "https://example.com"}
        )
    assert "access-control-allow-origin" not in {k.lower() for k in resp.headers}


def test_cors_allows_configured_origin(_settings_module, monkeypatch):
    monkeypatch.setattr(
        "tests.fixtures.test_settings.CORS_ALLOWED_ORIGINS",
        ["https://example.com"],
        raising=False,
    )
    app = create_app()
    with TestClient(app) as client:
        resp = client.get(
            "/openapi.json", headers={"Origin": "https://example.com"}
        )
    assert resp.headers.get("access-control-allow-origin") == "https://example.com"


def test_custom_middleware_from_settings_is_applied(_settings_module, monkeypatch):
    monkeypatch.setattr(
        "tests.fixtures.test_settings.MIDDLEWARE",
        ["tests.test_middleware._MarkerMiddleware"],
        raising=False,
    )
    app = create_app()
    with TestClient(app) as client:
        resp = client.get("/openapi.json")
    assert resp.headers.get("x-marker") == "hit"


def test_invalid_middleware_entry_raises_clear_error(_settings_module, monkeypatch):
    monkeypatch.setattr("tests.fixtures.test_settings.MIDDLEWARE", ["NotDotted"], raising=False)
    with pytest.raises(ImportError):
        create_app()
