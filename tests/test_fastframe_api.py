"""FastFrameAPI: function routes, resource routes, and model responses."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

from fastframe.http import FastFrameAPI
from fastframe.http.api import iter_routes
from fastframe.http.responses import encode_response


class UserCreate(BaseModel):
    name: str


def test_function_routes_register_explicit_paths() -> None:
    api = FastFrameAPI()

    @api.get("/users/{id}")
    def get_user(id: int) -> dict[str, int]:
        return {"id": id}

    @api.post("/users")
    def create_user(data: UserCreate) -> dict[str, str]:
        return {"name": data.name}

    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)

    assert client.get("/users/7").json() == {"id": 7}
    assert client.post("/users", json={"name": "Ada"}).json() == {"name": "Ada"}
    schema = app.openapi()
    assert "/users/{id}" in schema["paths"]
    assert "get" in schema["paths"]["/users/{id}"]
    assert "/users" in schema["paths"]


def test_resource_route_maps_verbs_and_ignores_other_methods() -> None:
    api = FastFrameAPI()

    @api.route("/users/{id}")
    class UserAPI:
        def get(self, id: int) -> dict[str, int]:
            return {"id": id}

        def delete(self, id: int) -> dict[str, bool]:
            return {"deleted": True}

        def helper(self) -> None:
            raise AssertionError("not a route")

    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)

    assert client.get("/users/3").json() == {"id": 3}
    assert client.delete("/users/3").json() == {"deleted": True}
    assert client.post("/users/3").status_code == 405
    methods = {route.methods.pop() for route in iter_routes(api) if route.path == "/users/{id}"}
    assert methods == {"GET", "DELETE"}


def test_class_name_is_not_a_path() -> None:
    api = FastFrameAPI()

    @api.route("/people")
    class UserAPI:
        def get(self) -> list[str]:
            return []

    assert [route.path for route in iter_routes(api)] == ["/people"]


def test_native_router_can_be_included() -> None:
    api = FastFrameAPI()
    native = APIRouter()

    @native.get("/native")
    def native_route() -> dict[str, bool]:
        return {"native": True}

    api.include_router(native)
    app = FastAPI()
    app.include_router(api.router)
    assert TestClient(app).get("/native").json() == {"native": True}


def test_response_model_is_forwarded() -> None:
    api = FastFrameAPI()

    class UserOut(BaseModel):
        id: int

    @api.get("/users/{id}", response_model=UserOut)
    def get_user(id: int) -> dict[str, int]:
        return {"id": id, "secret": "no"}

    app = FastAPI()
    app.include_router(api.router)
    assert TestClient(app).get("/users/1").json() == {"id": 1}


def test_encode_response_leaves_plain_values_alone() -> None:
    assert encode_response({"ok": True}) == {"ok": True}
    assert encode_response([1, 2]) == [1, 2]
    assert encode_response(None) is None


def test_installed_app_api_module_is_mounted(miniproject_env, tmp_path) -> None:
    api_file = miniproject_env / "posts" / "api.py"
    api_file.write_text(
        "from fastframe.http import FastFrameAPI\n"
        "api = FastFrameAPI()\n"
        "@api.get('/posts/ping')\n"
        "def ping() -> dict[str, bool]:\n"
        "    return {'pong': True}\n",
        encoding="utf-8",
    )
    try:
        from fastapi.testclient import TestClient

        from fastframe.http.asgi import get_asgi_application

        app = get_asgi_application()
        assert TestClient(app).get("/posts/ping").json() == {"pong": True}
    finally:
        api_file.unlink()
        for cached in ("posts.api",):
            import sys

            sys.modules.pop(cached, None)
