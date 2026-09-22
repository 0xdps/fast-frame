from __future__ import annotations


def test_shutdown_hook_runs_on_asgi_lifespan_shutdown(miniproject_env, monkeypatch) -> None:
    from config.asgi import application
    from fastapi.testclient import TestClient

    from fastframe.core.bootstrap import get_apps_registry

    calls: list[str] = []
    registry = get_apps_registry()
    health_config = registry.app_configs[0]
    monkeypatch.setattr(health_config, "shutdown", lambda: calls.append(health_config.label))

    with TestClient(application) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert calls == []  # not yet — shutdown only runs when the `with` block exits

    assert calls == [health_config.label]


def test_default_app_config_shutdown_is_a_noop() -> None:
    from fastframe.core.apps import AppConfig

    AppConfig().shutdown()  # should not raise


def test_caller_supplied_lifespan_is_not_overridden(miniproject_env) -> None:
    from contextlib import asynccontextmanager

    from fastapi.testclient import TestClient

    from fastframe.http.asgi import get_asgi_application

    calls: list[str] = []

    @asynccontextmanager
    async def custom_lifespan(app):
        calls.append("start")
        yield
        calls.append("stop")

    app = get_asgi_application(lifespan=custom_lifespan)

    with TestClient(app) as client:
        assert calls == ["start"]
        client.get("/health")

    assert calls == ["start", "stop"]
