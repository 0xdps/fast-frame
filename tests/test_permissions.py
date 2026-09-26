"""Tests for the opt-in, per-user permission system.

ModelAdmin.enforce_permissions = True switches has_*_permission from a
static bool (same for everyone) to a per-request check against permission
strings ("app_label.action_model") — own (User.permissions) plus every
Group the user belongs to. Superusers always pass.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastframe.admin import ModelAdmin, ensure_audit_log_registered
from fastframe.admin.site import AdminSite
from fastframe.contrib.auth.models import Group, User
from fastframe.contrib.auth.permissions import (
    get_effective_permissions,
    permission_codename,
    user_has_model_perm,
)
from fastframe.db.session import session_scope
from fastframe.models import Model, fields


class Widget(Model):
    name = fields.CharField(max_length=100)

    class Meta:
        db_table = "perm_widgets"
        app_label = "shop"


class WidgetAdmin(ModelAdmin):
    enforce_permissions = True


class Vault(Model):
    """A model whose deletion is hard-locked, even for a fully-permissioned user."""

    name = fields.CharField(max_length=100)

    class Meta:
        db_table = "perm_vaults"
        app_label = "shop"


class VaultAdmin(ModelAdmin):
    enforce_permissions = True
    # Hard override: nobody, ever — not even with the matching permission string.
    has_delete_permission = False


perm_site = AdminSite(name="test-permissions")
perm_site.register(Widget, WidgetAdmin)
perm_site.register(Vault, VaultAdmin)


@pytest.fixture
def app(miniproject_env, monkeypatch):
    monkeypatch.setattr("fastframe.admin.api.admin_site", perm_site)
    ensure_audit_log_registered()

    from fastframe.contrib.auth.tokens import Token  # noqa: F401 - registers table
    from fastframe.db.engine import get_engine

    Model.metadata.create_all(bind=get_engine())

    fastapi_app = FastAPI()
    from fastframe.api import get_rest_api_router, get_rest_auth_router

    fastapi_app.include_router(get_rest_auth_router())
    fastapi_app.include_router(get_rest_api_router())

    with session_scope():
        for obj in list(Widget.objects.all()):
            obj.delete()
        for obj in list(Vault.objects.all()):
            obj.delete()
        for group in list(Group.objects.all()):
            group.delete()
        for user in list(User.objects.all()):
            user.delete()

    return fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


def _create_user(username: str, *, permissions=None, groups=None, is_superuser=False) -> None:
    with session_scope():
        user = User(username=username, email=f"{username}@example.com", password="")
        user.set_password("s3cret-pass")
        if permissions:
            user.permissions = list(permissions)
        if is_superuser:
            user.is_superuser = True
        user.save()
        if groups:
            for group_name in groups:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)


def _create_group(name: str, permissions: list[str]) -> None:
    with session_scope():
        Group(name=name, permissions=permissions).save()


def _token_for(client, username: str, password: str = "s3cret-pass") -> str:
    resp = client.post("/api/auth/token", json={"username": username, "password": password})
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["token"]


# ----------------------------------------------------------------------
# permission_codename / get_effective_permissions / user_has_model_perm
# ----------------------------------------------------------------------


def test_permission_codename_format():
    assert permission_codename(Widget, "add") == "shop.add_widget"
    assert permission_codename(Widget, "delete") == "shop.delete_widget"


def test_get_effective_permissions_flattens_own_and_group_perms(miniproject_env):
    from fastframe.db.engine import get_engine

    Model.metadata.create_all(bind=get_engine())
    with session_scope():
        for user in list(User.objects.all()):
            user.delete()
        for group in list(Group.objects.all()):
            group.delete()

    _create_group("editors", ["shop.change_widget"])
    _create_user("bob", permissions=["shop.view_widget"], groups=["editors"])

    with session_scope():
        bob = User.objects.get(username="bob")
        effective = get_effective_permissions(bob)

    assert effective == {"shop.view_widget", "shop.change_widget"}


def test_user_has_model_perm_respects_superuser(miniproject_env):
    from fastframe.db.engine import get_engine

    Model.metadata.create_all(bind=get_engine())
    with session_scope():
        for user in list(User.objects.all()):
            user.delete()

    _create_user("root", is_superuser=True)
    with session_scope():
        root = User.objects.get(username="root")
        assert user_has_model_perm(root, Widget, "delete") is True


# ----------------------------------------------------------------------
# Enforcement through the REST API
# ----------------------------------------------------------------------


def test_enforced_model_denies_by_default(client):
    """A plain active user with no grants can't create on an
    enforce_permissions=True model — permission strings are opt-in, not
    opt-out."""
    _create_user("nobody")
    token = _token_for(client, "nobody")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/widget", json={"name": "gadget"}, headers=headers)
    assert resp.status_code == 403


def test_own_permission_grants_add(client):
    _create_user("alice", permissions=["shop.add_widget"])
    token = _token_for(client, "alice")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/widget", json={"name": "gadget"}, headers=headers)
    assert resp.status_code == 201


def test_group_permission_grants_change(client):
    _create_group("editors", ["shop.add_widget", "shop.change_widget"])
    _create_user("carol", groups=["editors"])
    token = _token_for(client, "carol")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post("/api/v1/widget", json={"name": "thing"}, headers=headers)
    assert create.status_code == 201
    widget_id = create.json()["data"]["id"]

    update = client.put(
        f"/api/v1/widget/{widget_id}", json={"name": "renamed"}, headers=headers
    )
    assert update.status_code == 200
    assert update.json()["data"]["name"] == "renamed"


def test_superuser_bypasses_all_permission_checks(client):
    _create_user("root", is_superuser=True)
    token = _token_for(client, "root")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post("/api/v1/widget", json={"name": "gadget"}, headers=headers)
    assert resp.status_code == 201


def test_missing_permission_denies_delete(client):
    _create_user("dave", permissions=["shop.add_widget"])
    token = _token_for(client, "dave")
    headers = {"Authorization": f"Bearer {token}"}

    create = client.post("/api/v1/widget", json={"name": "thing"}, headers=headers)
    widget_id = create.json()["data"]["id"]

    resp = client.delete(f"/api/v1/widget/{widget_id}", headers=headers)
    assert resp.status_code == 403


def test_list_endpoint_also_enforces_view_permission(client):
    """Regression: list_records used to skip the view-permission check
    entirely (only get_record checked it)."""
    _create_user("eve")
    token = _token_for(client, "eve")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/widget", headers=headers)
    assert resp.status_code == 403


def test_hard_override_denies_even_with_matching_permission(client):
    """has_delete_permission = False wins even when enforce_permissions is on
    and the user has been explicitly granted shop.delete_vault."""
    _create_user("root", is_superuser=True)
    _create_user("gary", permissions=["shop.add_vault", "shop.delete_vault"])

    admin_token = _token_for(client, "root")
    create = client.post(
        "/api/v1/vault",
        json={"name": "safe"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create.status_code == 201
    vault_id = create.json()["data"]["id"]

    gary_token = _token_for(client, "gary")
    resp = client.delete(
        f"/api/v1/vault/{vault_id}", headers={"Authorization": f"Bearer {gary_token}"}
    )
    assert resp.status_code == 403


def test_schema_permissions_reflect_current_user(client):
    _create_user("frank", permissions=["shop.add_widget"])
    token = _token_for(client, "frank")
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/api/v1/schema", headers=headers)
    assert resp.status_code == 200
    widget_schema = next(m for m in resp.json()["models"] if m["resource"] == "widget")
    assert widget_schema["permissions"]["create"] is True
    assert widget_schema["permissions"]["delete"] is False
