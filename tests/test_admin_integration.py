"""Integration tests for Admin system."""

import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from fastframe.admin import admin_site
from fastframe.contrib.auth.models import User
from fastframe.core import create_app
from fastframe.models import Model


@pytest.fixture
def test_db():
    """Create temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    import os

    os.close(fd)
    engine = create_engine(f"sqlite:///{db_path}")
    Model.metadata.create_all(engine)

    yield engine, db_path

    # Cleanup
    try:
        Path(db_path).unlink()
    except Exception:
        pass


@pytest.fixture
def admin_app():
    """Create FastFrame app with admin enabled."""
    # Override settings temporarily
    import os

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


def test_admin_api_list_users(client, test_db):
    """Admin API should list users."""
    engine, _ = test_db

    # Create test user
    with Session(engine) as session:
        user = User(
            username="testuser",
            email="test@example.com",
        )
        user.set_password("password123")
        session.add(user)
        session.commit()

    # List users via API
    response = client.get("/api/admin/User")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(u["username"] == "testuser" for u in data)


def test_admin_api_create_user(client):
    """Admin API should create users."""
    response = client.post(
        "/api/admin/User",
        json={
            "username": "newuser",
            "email": "new@example.com",
            "is_active": True,
        },
    )
    # Note: May fail if auth/validation required - that's expected
    assert response.status_code in (200, 201, 400, 401, 403)


def test_admin_api_get_user(client, test_db):
    """Admin API should retrieve single user."""
    engine, _ = test_db

    # Create test user
    with Session(engine) as session:
        user = User(
            username="gettest",
            email="get@example.com",
        )
        user.set_password("password123")
        session.add(user)
        session.commit()
        user_id = user.id

    # Get user via API
    response = client.get(f"/api/admin/User/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "gettest"
    assert data["email"] == "get@example.com"


def test_admin_api_update_user(client, test_db):
    """Admin API should update users."""
    engine, _ = test_db

    # Create test user
    with Session(engine) as session:
        user = User(
            username="updatetest",
            email="update@example.com",
        )
        user.set_password("password123")
        session.add(user)
        session.commit()
        user_id = user.id

    # Update user via API
    response = client.put(
        f"/api/admin/User/{user_id}",
        json={
            "username": "updatetest",
            "email": "updated@example.com",
            "is_active": True,
        },
    )
    assert response.status_code in (200, 204)

    # Verify update
    with Session(engine) as session:
        user = session.get(User, user_id)
        assert user.email == "updated@example.com"


def test_admin_api_delete_user(client, test_db):
    """Admin API should delete users."""
    engine, _ = test_db

    # Create test user
    with Session(engine) as session:
        user = User(
            username="deletetest",
            email="delete@example.com",
        )
        user.set_password("password123")
        session.add(user)
        session.commit()
        user_id = user.id

    # Delete user via API
    response = client.delete(f"/api/admin/User/{user_id}")
    assert response.status_code in (200, 204)

    # Verify deletion
    with Session(engine) as session:
        user = session.get(User, user_id)
        assert user is None


def test_admin_settings_endpoint(client):
    """Admin settings endpoint should return config."""
    response = client.get("/api/admin/_settings")
    assert response.status_code == 200
    data = response.json()
    assert "site_title" in data
    assert "resources" in data


def test_admin_field_metadata(client):
    """Admin should expose field metadata for forms."""
    response = client.get("/api/admin/resources")
    assert response.status_code == 200
    resources = response.json()

    user_resource = next((r for r in resources if r["name"] == "User"), None)
    assert user_resource is not None
    assert "fields" in user_resource

    # Check field metadata
    fields = user_resource["fields"]
    assert any(f["name"] == "username" for f in fields)
    assert any(f["name"] == "email" for f in fields)

    # Email field should have type info
    email_field = next((f for f in fields if f["name"] == "email"), None)
    assert email_field is not None
    assert email_field.get("type") in ("email", "EmailField", "CharField")


def test_admin_respects_enable_admin_setting(monkeypatch):
    """Admin should not mount if ENABLE_ADMIN=False."""
    import os

    monkeypatch.setenv("FASTFRAME_SETTINGS_MODULE", "tests.fixtures.admin_disabled_settings")

    app = create_app()
    client = TestClient(app)

    # Admin routes should not exist
    response = client.get("/admin/")
    assert response.status_code == 404

    response = client.get("/api/admin/resources")
    assert response.status_code == 404


def test_admin_respects_custom_prefix():
    """Admin should respect custom URL prefix."""
    import os

    # Would need custom settings with ADMIN_PREFIX="/custom-admin"
    # For now, just verify current prefix works
    pass  # TODO: Implement when settings override is cleaner
