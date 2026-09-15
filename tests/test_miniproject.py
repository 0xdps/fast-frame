from __future__ import annotations

from fastapi.testclient import TestClient


def test_bootstrap_loads_apps(miniproject_env) -> None:
    from fastframe.core.bootstrap import bootstrap, get_apps_registry

    registry = bootstrap(None)
    assert len(registry.app_configs) == 3  # health, users, posts
    assert registry.app_configs[0].label == "health"
    assert get_apps_registry() is registry


def test_health_endpoint(miniproject_env) -> None:
    from config.asgi import application

    client = TestClient(application)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_check_command(miniproject_env, capsys) -> None:
    import argparse

    from fastframe.cli.commands.check import execute

    execute(argparse.Namespace())
    out = capsys.readouterr().out
    assert "health" in out
    assert "no issues" in out
