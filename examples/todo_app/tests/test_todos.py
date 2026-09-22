from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_and_list_todo(client: TestClient) -> None:
    resp = client.post("/todos", json={"title": "Buy milk"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "Buy milk"
    assert body["done"] is False

    resp = client.get("/todos")
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_update_todo(client: TestClient) -> None:
    todo = client.post("/todos", json={"title": "Write docs"}).json()

    resp = client.patch(f"/todos/{todo['id']}", json={"done": True})
    assert resp.status_code == 200
    assert resp.json()["done"] is True


def test_get_missing_todo_returns_404(client: TestClient) -> None:
    resp = client.get("/todos/999")
    assert resp.status_code == 404


def test_delete_todo(client: TestClient) -> None:
    todo = client.post("/todos", json={"title": "Temp"}).json()

    resp = client.delete(f"/todos/{todo['id']}")
    assert resp.status_code == 204

    resp = client.get(f"/todos/{todo['id']}")
    assert resp.status_code == 404


def test_filter_by_done(client: TestClient) -> None:
    a = client.post("/todos", json={"title": "A"}).json()
    client.post("/todos", json={"title": "B"})
    client.patch(f"/todos/{a['id']}", json={"done": True})

    resp = client.get("/todos", params={"done": "true"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["title"] == "A"
