"""Integration tests for admin authentication (login/logout/session)."""

import os

import pytest
from fastapi.testclient import TestClient

from fastframe.contrib.auth.models import User
from fastframe.core import create_app
from fastframe.models import Model


@pytest.fixture
def auth_admin_app():
    """Create a FastFrame app with admin auth enabled."""
    original_settings = os.environ.get("FASTFRAME_SETTINGS_MODULE")
    os.environ["FASTFRAME_SETTINGS_MODULE"] = "tests.fixtures.admin_auth_test_settings"

    try:
        app = create_app()
        yield app
    finally:
        if original_settings:
            os.environ["FASTFRAME_SETTINGS_MODULE"] = original_settings
        else:
            os.environ.pop("FASTFRAME_SETTINGS_MODULE", None)


@pytest.fixture
def client(auth_admin_app):
    """Test client against the auth-enabled admin app."""
    with TestClient(auth_admin_app) as c:
        yield c


def _reset_users() -> None:
    from fastframe.db.engine import get_engine
    from fastframe.db.session import session_scope

    Model.metadata.create_all(bind=get_engine())
    with session_scope():
        for user in list(User.objects.all()):
            user.delete()


def _create_admin_user(username="admin", password="s3cret-pass", can_access_admin=True):
    from fastframe.db.session import session_scope

    with session_scope():
        user = User(username=username, email=f"{username}@example.com", password="")
        user.set_password(password)
        user.can_access_admin = can_access_admin
        user.save()
        return user.id


def test_protected_endpoint_requires_login(client):
    """Hitting a CRUD endpoint without a session should return 401."""
    _reset_users()
    response = client.get("/api/admin/user")
    assert response.status_code == 401


def test_me_requires_login(client):
    """/api/admin/me should 401 when not logged in."""
    _reset_users()
    response = client.get("/api/admin/me")
    assert response.status_code == 401


def test_login_with_bad_credentials_rejected(client):
    """Login with wrong password should 401 and not set a cookie."""
    _reset_users()
    _create_admin_user(username="admin1", password="correct-pass")

    response = client.post(
        "/api/admin/login",
        json={"username": "admin1", "password": "wrong-pass"},
    )
    assert response.status_code == 401
    assert "ff_admin_session" not in response.cookies


def test_login_without_admin_access_forbidden(client):
    """Login succeeds credential-wise, but 403 if the user lacks admin access."""
    _reset_users()
    _create_admin_user(username="regular", password="correct-pass", can_access_admin=False)

    response = client.post(
        "/api/admin/login",
        json={"username": "regular", "password": "correct-pass"},
    )
    assert response.status_code == 403


def test_login_success_sets_cookie_and_unlocks_api(client):
    """A valid admin login sets a session cookie that unlocks protected routes."""
    _reset_users()
    _create_admin_user(username="admin2", password="correct-pass")

    login_response = client.post(
        "/api/admin/login",
        json={"username": "admin2", "password": "correct-pass"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["data"]["username"] == "admin2"
    assert "ff_admin_session" in login_response.cookies

    # Now the same client (cookie persists) can hit protected routes.
    me_response = client.get("/api/admin/me")
    assert me_response.status_code == 200
    assert me_response.json()["data"]["username"] == "admin2"

    list_response = client.get("/api/admin/user")
    assert list_response.status_code == 200


def test_logout_clears_session(client):
    """After logout, protected routes should 401 again."""
    _reset_users()
    _create_admin_user(username="admin3", password="correct-pass")

    client.post("/api/admin/login", json={"username": "admin3", "password": "correct-pass"})
    assert client.get("/api/admin/me").status_code == 200

    logout_response = client.post("/api/admin/logout")
    assert logout_response.status_code == 200

    assert client.get("/api/admin/me").status_code == 401


def test_unauthenticated_admin_ui_shows_login_page(client):
    """The static admin SPA route serves a login page when not authenticated."""
    _reset_users()
    response = client.get("/admin/")
    assert response.status_code == 200
    assert "login" in response.text.lower()
