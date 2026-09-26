"""Tests for the token-authenticated generic REST API (src/fastframe/api/).

Mirrors tests/test_admin_api.py's structure, but exercises the token-auth
surface: obtaining/revoking tokens and CRUD through fastframe.api instead
of the cookie-session admin API. Since both share admin_site's registry
and _build_crud_router, this focuses on what's different: auth mechanics
and any-active-user access, not re-testing every CRUD edge case.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastframe.admin import ModelAdmin, ensure_audit_log_registered
from fastframe.admin.audit import AuditLog
from fastframe.admin.site import AdminSite
from fastframe.api import get_rest_api_router, get_rest_auth_router
from fastframe.contrib.auth.models import User
from fastframe.contrib.auth.tokens import Token  # noqa: F401 - import registers the table
from fastframe.db.session import session_scope
from fastframe.models import Model, fields

# ----------------------------------------------------------------------
# Module-level models (created once)
# ----------------------------------------------------------------------


class RestWidget(Model):
    name = fields.CharField(max_length=100)
    stock = fields.IntegerField(default=0)

    class Meta:
        db_table = "rest_widgets"
        verbose_name = "Widget"
        verbose_name_plural = "Widgets"


class RestWidgetAdmin(ModelAdmin):
    list_display = ["name", "stock"]
    search_fields = ["name"]


test_site = AdminSite(name="test-rest-api")
test_site.register(RestWidget, RestWidgetAdmin)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def app(miniproject_env, monkeypatch):
    """Bare FastAPI app with the token auth + REST API routers mounted."""
    monkeypatch.setattr("fastframe.admin.api.admin_site", test_site)
    ensure_audit_log_registered()

    from fastframe.db.engine import get_engine

    Model.metadata.create_all(bind=get_engine())

    fastapi_app = FastAPI()
    fastapi_app.include_router(get_rest_auth_router())
    fastapi_app.include_router(get_rest_api_router())

    with session_scope():
        for obj in list(RestWidget.objects.all()):
            obj.delete()
        for user in list(User.objects.all()):
            user.delete()
        for entry in list(AuditLog.objects.all()):
            entry.delete()

    return fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


def _create_user(username="alice", password="s3cret-pass", is_active=True):
    with session_scope():
        user = User(username=username, email=f"{username}@example.com", password="")
        user.set_password(password)
        user.is_active = is_active
        user.save()
        return user.id


# ----------------------------------------------------------------------
# Token obtain / revoke
# ----------------------------------------------------------------------


def test_obtain_token_with_valid_credentials(client):
    _create_user()
    resp = client.post("/api/auth/token", json={"username": "alice", "password": "s3cret-pass"})
    assert resp.status_code == 201
    token = resp.json()["data"]["token"]
    assert isinstance(token, str) and len(token) == 64


def test_obtain_token_with_bad_credentials(client):
    _create_user()
    resp = client.post("/api/auth/token", json={"username": "alice", "password": "wrong"})
    assert resp.status_code == 401


def test_obtain_token_for_inactive_user_still_issues_but_cannot_authenticate(client):
    """authenticate() already rejects inactive users at login time."""
    _create_user(is_active=False)
    resp = client.post("/api/auth/token", json={"username": "alice", "password": "s3cret-pass"})
    assert resp.status_code == 401


def test_revoke_token(client):
    _create_user()
    token = client.post(
        "/api/auth/token", json={"username": "alice", "password": "s3cret-pass"}
    ).json()["data"]["token"]

    resp = client.get("/api/v1/restwidget", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    revoke = client.delete("/api/auth/token", headers={"Authorization": f"Bearer {token}"})
    assert revoke.status_code == 200

    resp = client.get("/api/v1/restwidget", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 401


def test_revoke_unknown_token_404(client):
    resp = client.delete("/api/auth/token", headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 404


# ----------------------------------------------------------------------
# CRUD, token-authenticated
# ----------------------------------------------------------------------


def _auth_headers(client, username="alice", password="s3cret-pass") -> dict:
    token = client.post(
        "/api/auth/token", json={"username": username, "password": password}
    ).json()["data"]["token"]
    return {"Authorization": f"Bearer {token}"}


def test_crud_without_token_401(client):
    resp = client.get("/api/v1/restwidget")
    assert resp.status_code == 401


def test_crud_with_malformed_header_401(client):
    resp = client.get("/api/v1/restwidget", headers={"Authorization": "NotBearer xyz"})
    assert resp.status_code == 401


def test_any_active_user_can_list(client):
    """Unlike admin, no can_access_admin / staff flag is required."""
    _create_user()
    headers = _auth_headers(client)
    resp = client.get("/api/v1/restwidget", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == {"data": [], "total": 0, "page": 1, "perPage": 25}


def test_create_update_delete_via_token(client):
    _create_user()
    headers = _auth_headers(client)

    create_resp = client.post(
        "/api/v1/restwidget", json={"name": "Bolt", "stock": 10}, headers=headers
    )
    assert create_resp.status_code == 201
    widget_id = create_resp.json()["data"]["id"]

    update_resp = client.put(
        f"/api/v1/restwidget/{widget_id}", json={"stock": 5}, headers=headers
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["data"]["stock"] == 5

    delete_resp = client.delete(f"/api/v1/restwidget/{widget_id}", headers=headers)
    assert delete_resp.status_code == 200

    get_resp = client.get(f"/api/v1/restwidget/{widget_id}", headers=headers)
    assert get_resp.status_code == 404


def test_schema_reachable_via_token(client):
    """The REST API exposes the same registry/schema as admin."""
    _create_user()
    headers = _auth_headers(client)
    resp = client.get("/api/v1/schema", headers=headers)
    assert resp.status_code == 200
    resources = {m["resource"] for m in resp.json()["models"]}
    assert "restwidget" in resources


# ----------------------------------------------------------------------
# Audit log — writes happen regardless of which surface (admin vs API)
# ----------------------------------------------------------------------


def test_create_via_token_writes_audit_log(client):
    _create_user()
    headers = _auth_headers(client)
    resp = client.post("/api/v1/restwidget", json={"name": "Nut", "stock": 3}, headers=headers)
    widget_id = resp.json()["data"]["id"]

    with session_scope():
        entries = list(AuditLog.objects.filter(action="create", model_name="RestWidget"))
        assert len(entries) == 1
        entry = entries[0]
        assert entry.username == "alice"
        assert entry.source == "api"
        assert entry.object_id == str(widget_id)
        assert entry.changes["fields"]["name"] == "Nut"


def test_update_via_token_writes_diff(client):
    _create_user()
    headers = _auth_headers(client)
    widget_id = client.post(
        "/api/v1/restwidget", json={"name": "Screw", "stock": 1}, headers=headers
    ).json()["data"]["id"]

    with session_scope():
        for entry in list(AuditLog.objects.filter(model_name="RestWidget")):
            entry.delete()

    client.put(f"/api/v1/restwidget/{widget_id}", json={"stock": 99}, headers=headers)

    with session_scope():
        entry = AuditLog.objects.get(action="update", model_name="RestWidget")
        assert entry.changes["stock"] == {"old": 1, "new": 99}
        assert "name" not in entry.changes  # unchanged fields aren't in the diff


def test_delete_via_token_writes_audit_log_with_snapshot(client):
    _create_user()
    headers = _auth_headers(client)
    widget_id = client.post(
        "/api/v1/restwidget", json={"name": "Washer", "stock": 7}, headers=headers
    ).json()["data"]["id"]

    with session_scope():
        for entry in list(AuditLog.objects.filter(model_name="RestWidget", action="create")):
            entry.delete()

    client.delete(f"/api/v1/restwidget/{widget_id}", headers=headers)

    with session_scope():
        entry = AuditLog.objects.get(action="delete", model_name="RestWidget")
        assert entry.object_id == str(widget_id)
        assert entry.changes["fields"]["name"] == "Washer"


def test_audit_log_is_read_only_in_admin_config():
    from fastframe.admin.audit import AuditLogAdmin

    assert AuditLogAdmin.has_add_permission is False
    assert AuditLogAdmin.has_change_permission is False
    assert AuditLogAdmin.has_delete_permission is False
