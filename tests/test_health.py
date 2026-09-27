"""Tests for the built-in ``fastframe.health`` app."""

from __future__ import annotations


def test_health_router_default(miniproject_env) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from fastframe.health.views import get_health_router

    app = FastAPI()
    app.include_router(get_health_router())
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_overridable_via_dotted_path(miniproject_env, tmp_path) -> None:
    """HEALTH_CHECK can point at a project callable returning a custom body."""
    import sys

    module = tmp_path / "myhealth.py"
    module.write_text(
        'def custom_check() -> dict:\n    return {"app": "custom", "healthy": True}\n',
        encoding="utf-8",
    )
    sys.path.insert(0, str(tmp_path))

    from fastframe.conf import settings as conf_settings

    conf_settings.HEALTH_CHECK = "myhealth.custom_check"
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from fastframe.health.views import get_health_router

        app = FastAPI()
        app.include_router(get_health_router())
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"app": "custom", "healthy": True}
    finally:
        conf_settings.HEALTH_CHECK = None


def test_health_path_overridable(miniproject_env) -> None:
    from fastframe.conf import settings as conf_settings

    conf_settings.HEALTH_PATH = "/status"
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from fastframe.health.views import get_health_router

        app = FastAPI()
        app.include_router(get_health_router())
        client = TestClient(app)
        assert client.get("/status").status_code == 200
        assert client.get("/health").status_code == 404
    finally:
        conf_settings.HEALTH_PATH = "/health"