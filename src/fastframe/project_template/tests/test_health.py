from fastapi.testclient import TestClient


def test_health_endpoint(project_env) -> None:
    from config.asgi import application

    client = TestClient(application)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
