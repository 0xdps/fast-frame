"""Tests for the admin UI shell gating (src/fastframe/admin/views.py).

Three states for ``GET /admin``:

* No session at all               -> login page (200, login form)
* Session, ``can_access_admin``   -> the real SPA shell (200, index.html)
* Session, not ``can_access_admin`` -> access-denied page (403), not the SPA

The third case is the one that previously fell through to the SPA shell
(gated on "any session" via ``get_current_admin_user`` instead of
``can_access_admin``), which then 403'd on every API call the SPA made.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastframe.admin import get_admin_auth_router, get_admin_router
from fastframe.contrib.auth.models import User
from fastframe.contrib.auth.views import get_auth_router
from fastframe.db.session import session_scope


@pytest.fixture
def app(miniproject_env):
    """FastAPI app with the admin UI shell + both login routers mounted."""
    from fastframe.db.engine import get_engine
    from fastframe.models import Model

    # miniproject's INSTALLED_APPS/migrations don't include fastframe.contrib.auth,
    # so create the User table ourselves (mirrors tests/test_admin_api.py).
    Model.metadata.create_all(bind=get_engine())

    fastapi_app = FastAPI()
    fastapi_app.include_router(get_admin_auth_router())
    fastapi_app.include_router(get_auth_router())
    fastapi_app.include_router(get_admin_router())

    with session_scope():
        for user in list(User.objects.all()):
            user.delete()

        admin_user = User(username="admin", email="admin@example.com", password="")
        admin_user.set_password("s3cret-pass")
        admin_user.can_access_admin = True
        admin_user.save()

        plain_user = User(username="plain", email="plain@example.com", password="")
        plain_user.set_password("s3cret-pass")
        plain_user.can_access_admin = False
        plain_user.save()

    return fastapi_app


def test_admin_shell_shows_login_page_when_logged_out(app):
    client = TestClient(app)
    resp = client.get("/admin/")
    assert resp.status_code == 200
    assert "login-form" in resp.text


def test_admin_shell_serves_spa_for_can_access_admin_user(app):
    client = TestClient(app)
    login = client.post("/api/admin/login", json={"username": "admin", "password": "s3cret-pass"})
    assert login.status_code == 200

    resp = client.get("/admin/")
    assert resp.status_code == 200
    assert "login-form" not in resp.text


def test_admin_shell_denies_logged_in_user_without_admin_access(app):
    """A general-auth session for a non-admin user must not reach the SPA.

    Logging in via the *general* auth login (not the admin login, which
    itself enforces can_access_admin) is the realistic way a user ends up
    with a valid session but no admin access, e.g. after visiting /admin
    from a logged-in area of the main app.
    """
    client = TestClient(app)
    login = client.post("/api/auth/login", json={"username": "plain", "password": "s3cret-pass"})
    assert login.status_code == 200

    resp = client.get("/admin/")
    assert resp.status_code == 403
    assert "login-form" not in resp.text
    assert "doesn&#x27;t have admin access" in resp.text or "doesn't have admin access" in resp.text
