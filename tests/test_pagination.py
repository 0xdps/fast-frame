from __future__ import annotations

from fastframe.http.pagination import Pagination


def test_pagination_apply_calls_limit_then_offset() -> None:
    calls: list[tuple[str, int]] = []

    class FakeQuerySet:
        def limit(self, n: int) -> FakeQuerySet:
            calls.append(("limit", n))
            return self

        def offset(self, n: int) -> FakeQuerySet:
            calls.append(("offset", n))
            return self

    page = Pagination(limit=10, offset=5)
    page.apply(FakeQuerySet())

    assert calls == [("limit", 10), ("offset", 5)]


def test_pagination_dependency_end_to_end(miniproject_env) -> None:
    from config.asgi import application
    from fastapi import APIRouter, Depends
    from fastapi.testclient import TestClient
    from users.models import User

    from fastframe.db.session import session_scope
    from fastframe.http.pagination import pagination

    with session_scope():
        for i in range(5):
            User.objects.create(email=f"user{i}@example.com", is_active=True)

    router = APIRouter()

    @router.get("/paged-users")
    def list_users(page: Pagination = Depends(pagination)) -> list[str]:
        users = page.apply(User.objects.order_by("email"))
        return [u.email for u in users]

    application.include_router(router)
    client = TestClient(application)

    response = client.get("/paged-users", params={"limit": 2, "offset": 1})
    assert response.status_code == 200
    assert response.json() == ["user1@example.com", "user2@example.com"]


def test_pagination_defaults(miniproject_env) -> None:
    from config.asgi import application
    from fastapi import APIRouter, Depends
    from fastapi.testclient import TestClient

    from fastframe.http.pagination import pagination

    router = APIRouter()

    @router.get("/pagination-echo")
    def echo(page: Pagination = Depends(pagination)) -> dict[str, int]:
        return {"limit": page.limit, "offset": page.offset}

    application.include_router(router)
    client = TestClient(application)

    response = client.get("/pagination-echo")
    assert response.json() == {"limit": 20, "offset": 0}


def test_pagination_rejects_limit_over_max(miniproject_env) -> None:
    from config.asgi import application
    from fastapi import APIRouter, Depends
    from fastapi.testclient import TestClient

    from fastframe.http.pagination import pagination

    router = APIRouter()

    @router.get("/pagination-echo2")
    def echo(page: Pagination = Depends(pagination)) -> dict[str, int]:
        return {"limit": page.limit, "offset": page.offset}

    application.include_router(router)
    client = TestClient(application)

    response = client.get("/pagination-echo2", params={"limit": 1000})
    assert response.status_code == 422
