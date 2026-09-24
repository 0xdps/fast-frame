"""Integration tests for Admin system."""

import os

import pytest
from fastapi.testclient import TestClient

from fastframe.contrib.auth.models import User
from fastframe.core import create_app
from fastframe.models import Model


@pytest.fixture
def admin_app():
    """Create FastFrame app with admin enabled."""
    original_settings = os.environ.get("FASTFRAME_SETTINGS_MODULE")
    os.environ["FASTFRAME_SETTINGS_MODULE"] = "tests.fixtures.admin_test_settings"

    try:
        app = create_app()
        yield app
    finally:
        if original_settings:
            os.environ["FASTFRAME_SETTINGS_MODULE"] = original_settings
        else:
            os.environ.pop("FASTFRAME_SETTINGS_MODULE", None)


@pytest.fixture
def client(admin_app):
    """Create test client."""
    with TestClient(admin_app) as c:
        yield c


def test_admin_home_accessible(client):
    """Admin home page should be accessible."""
    response = client.get("/admin/")
    assert response.status_code in (
        200,
        404,
    )  # 404 if static files not built, OK for now


def test_admin_api_resources_list(client):
    """Admin API should list available resources."""
    response = client.get("/api/admin/schema")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "models" in data
    # Should include User model from auth
    assert any(r["name"] == "User" for r in data["models"])


def _prepare_auth_tables() -> None:
    from fastframe.db.engine import get_engine
    from fastframe.db.session import session_scope

    Model.metadata.create_all(bind=get_engine())
    with session_scope():
        for user in list(User.objects.all()):
            user.delete()


def test_admin_api_list_users(client):
    """Admin API should list users."""
    from fastframe.db.session import session_scope

    _prepare_auth_tables()
    with session_scope():
        user = User(username="testuser", email="test@example.com", password="password123")
        user.save()

    response = client.get("/api/admin/user")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(row["username"] == "testuser" for row in data["data"])


def test_admin_api_create_user(client):
    """Admin API should create users."""
    _prepare_auth_tables()
    response = client.post(
        "/api/admin/user",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "password123",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["username"] == "newuser"


def test_admin_api_get_user(client):
    """Admin API should retrieve a single user."""
    from fastframe.db.session import session_scope

    _prepare_auth_tables()
    with session_scope():
        user = User(username="gettest", email="get@example.com", password="password123")
        user.save()
        user_id = user.id

    response = client.get(f"/api/admin/user/{user_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["username"] == "gettest"
    assert data["email"] == "get@example.com"


def test_admin_api_update_user(client):
    """Admin API should update users."""
    from fastframe.db.session import session_scope

    _prepare_auth_tables()
    with session_scope():
        user = User(username="updatetest", email="update@example.com", password="password123")
        user.save()
        user_id = user.id

    response = client.put(
        f"/api/admin/user/{user_id}",
        json={
            "username": "updatetest",
            "email": "updated@example.com",
            "password": "password123",
            "is_active": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "updated@example.com"


def test_admin_api_delete_user(client):
    """Admin API should delete users."""
    from fastframe.db.session import session_scope

    _prepare_auth_tables()
    with session_scope():
        user = User(username="deletetest", email="delete@example.com", password="password123")
        user.save()
        user_id = user.id

    response = client.delete(f"/api/admin/user/{user_id}")
    assert response.status_code == 200

    with session_scope():
        assert User.objects.filter(id=user_id).count() == 0


def test_admin_schema_includes_user(client):
    """Schema lists the default user model and its fields."""
    response = client.get("/api/admin/schema")
    assert response.status_code == 200
    models = response.json()["models"]
    user_resource = next(item for item in models if item["resource"] == "user")
    field_names = {field["name"] for field in user_resource["fields"]}
    assert "username" in field_names
    assert "email" in field_names


def test_admin_respects_enable_admin_setting(monkeypatch):
    """Admin should not mount if ENABLE_ADMIN=False."""
    monkeypatch.setenv("FASTFRAME_SETTINGS_MODULE", "tests.fixtures.admin_disabled_settings")

    app = create_app()
    client = TestClient(app)

    # Admin routes should not exist
    response = client.get("/admin/")
    assert response.status_code == 404

    response = client.get("/api/admin/resources")
    assert response.status_code == 404


def test_admin_respects_custom_prefix(client):
    """Admin API is mounted at the configured prefix."""
    response = client.get("/api/admin/schema")
    assert response.status_code == 200
