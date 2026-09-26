"""Tests for general-purpose session auth (outside /admin).

/api/auth/login|logout|me (fastframe.contrib.auth.views) and the
login_required/permission_required dependencies any app route can use
(fastframe.contrib.auth.dependencies) — same session cookie as the admin,
but without requiring can_access_admin.
"""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from fastframe.contrib.auth.dependencies import login_required, permission_required
from fastframe.contrib.auth.models import User
from fastframe.contrib.auth.views import get_auth_router
from fastframe.db.session import session_scope
from fastframe.models import Model


@pytest.fixture
def app(miniproject_env):
    from fastframe.db.engine import get_engine

    Model.metadata.create_all(bind=get_engine())

    fastapi_app = FastAPI()
    fastapi_app.include_router(get_auth_router())

    @fastapi_app.get("/whoami")
    def whoami(user=Depends(login_required)):
        return {"username": user.username}

    @fastapi_app.get("/reports")
    def reports(user=Depends(permission_required("reports.view_report"))):
        return {"username": user.username}

    with session_scope():
        for user in list(User.objects.all()):
            user.delete()

    return fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


def _create_user(username="dana", password="s3cret-pass", *, can_access_admin=False):
    with session_scope():
        user = User(username=username, email=f"{username}@example.com", password="")
        user.set_password(password)
        user.can_access_admin = can_access_admin
        user.save()
        return user.id


def test_login_sets_cookie_and_unlocks_app_route(client):
    _create_user()

    login = client.post("/api/auth/login", json={"username": "dana", "password": "s3cret-pass"})
    assert login.status_code == 200
    assert login.json()["data"]["username"] == "dana"

    who = client.get("/whoami")
    assert who.status_code == 200
    assert who.json()["username"] == "dana"


def test_login_does_not_require_admin_access(client):
    """Unlike /api/admin/login, this succeeds for a non-admin user."""
    _create_user(can_access_admin=False)
    login = client.post("/api/auth/login", json={"username": "dana", "password": "s3cret-pass"})
    assert login.status_code == 200


def test_login_required_route_401_without_session(client):
    resp = client.get("/whoami")
    assert resp.status_code == 401


def test_me_endpoint(client):
    _create_user()
    client.post("/api/auth/login", json={"username": "dana", "password": "s3cret-pass"})
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["data"]["username"] == "dana"


def test_logout_clears_session(client):
    _create_user()
    client.post("/api/auth/login", json={"username": "dana", "password": "s3cret-pass"})
    assert client.get("/whoami").status_code == 200

    client.post("/api/auth/logout")
    assert client.get("/whoami").status_code == 401


def test_permission_required_denies_without_permission(client):
    _create_user()
    client.post("/api/auth/login", json={"username": "dana", "password": "s3cret-pass"})
    resp = client.get("/reports")
    assert resp.status_code == 403


def test_permission_required_allows_with_permission(client):
    with session_scope():
        user = User(username="rob", email="rob@example.com", password="")
        user.set_password("s3cret-pass")
        user.permissions = ["reports.view_report"]
        user.save()

    client.post("/api/auth/login", json={"username": "rob", "password": "s3cret-pass"})
    resp = client.get("/reports")
    assert resp.status_code == 200


def test_admin_session_also_works_on_general_routes(client):
    """One session, both surfaces: an admin-login cookie also passes
    login_required on a plain app route."""
    from fastframe.admin.auth import get_admin_auth_router

    client.app.include_router(get_admin_auth_router())
    _create_user(username="adminish", can_access_admin=True)

    login = client.post(
        "/api/admin/login", json={"username": "adminish", "password": "s3cret-pass"}
    )
    assert login.status_code == 200

    who = client.get("/whoami")
    assert who.status_code == 200
    assert who.json()["username"] == "adminish"


def test_invalidate_sessions_revokes_existing_cookie(client):
    """User.invalidate_sessions() makes a previously issued session cookie
    stop working immediately, without touching other users' sessions."""
    _create_user()
    client.post("/api/auth/login", json={"username": "dana", "password": "s3cret-pass"})
    assert client.get("/whoami").status_code == 200

    with session_scope():
        user = User.objects.get(username="dana")
        user.invalidate_sessions()
        user.save()

    assert client.get("/whoami").status_code == 401


def test_inactive_user_session_rejected(client):
    _create_user()
    client.post("/api/auth/login", json={"username": "dana", "password": "s3cret-pass"})
    assert client.get("/whoami").status_code == 200

    with session_scope():
        user = User.objects.get(username="dana")
        user.is_active = False
        user.save()

    assert client.get("/whoami").status_code == 401
