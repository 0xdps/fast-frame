from __future__ import annotations


def test_does_not_exist_returns_404(miniproject_env) -> None:
    from config.asgi import application
    from fastapi.testclient import TestClient

    client = TestClient(application)
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"].lower()
