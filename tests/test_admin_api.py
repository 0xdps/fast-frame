"""Tests for the Admin REST API (src/fastframe/admin/api.py).

Models and the AdminSite are defined once at module level to avoid
SQLAlchemy's "table already defined" errors from re-creating classes.
Data is cleaned between tests by deleting all rows.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastframe.admin import ModelAdmin, get_admin_api_router, get_admin_auth_router
from fastframe.admin.audit import AuditLog
from fastframe.admin.site import AdminSite
from fastframe.contrib.auth.models import User
from fastframe.db.session import session_scope
from fastframe.models import Model, fields

# ----------------------------------------------------------------------
# Module-level models (created once)
# ----------------------------------------------------------------------


class ApiAuthor(Model):
    name = fields.CharField(max_length=100)
    email = fields.EmailField()

    class Meta:
        db_table = "api_authors"
        verbose_name = "Author"
        verbose_name_plural = "Authors"


class ApiBook(Model):
    title = fields.CharField(max_length=200)
    status = fields.CharField(
        max_length=20,
        default="draft",
        choices=[("draft", "Draft"), ("published", "Published")],
    )
    pages = fields.IntegerField(default=0)
    is_active = fields.BooleanField(default=True)

    class Meta:
        db_table = "api_books"
        verbose_name = "Book"
        verbose_name_plural = "Books"


class ApiAuthorAdmin(ModelAdmin):
    list_display = ["name", "email"]
    search_fields = ["name", "email"]


class ApiBookAdmin(ModelAdmin):
    list_display = ["title", "status", "pages"]
    search_fields = ["title"]
    list_filter = ["status"]


test_site = AdminSite(name="test-api")
test_site.register(ApiAuthor, ApiAuthorAdmin)
test_site.register(ApiBook, ApiBookAdmin)


# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture
def client(miniproject_env, monkeypatch):
    """TestClient with admin API mounted, isolated AdminSite, clean tables.

    Admin auth is always required, so this logs in an admin user before
    returning the client — the session cookie then rides along on every
    request made with it (see fastframe.admin.auth).
    """
    monkeypatch.setattr("fastframe.admin.api.admin_site", test_site)

    # This test builds a bare FastAPI() app directly rather than going
    # through create_app()/include_admin(), so register the audit log
    # model ourselves before create_all() (mirrors what include_admin() does).
    from fastframe.admin import ensure_audit_log_registered

    ensure_audit_log_registered()

    # Create tables for our module-level models (miniproject only migrates its own)
    from fastframe.db.engine import get_engine

    engine = get_engine()
    Model.metadata.create_all(bind=engine)

    app = FastAPI()
    app.include_router(get_admin_auth_router())
    app.include_router(get_admin_api_router())

    # Clean tables before each test
    with session_scope():
        for obj in list(ApiBook.objects.all()):
            obj.delete()
        for obj in list(ApiAuthor.objects.all()):
            obj.delete()
        for entry in list(AuditLog.objects.all()):
            entry.delete()
        for user in list(User.objects.all()):
            user.delete()
        admin_user = User(username="admin", email="admin@example.com", password="")
        admin_user.set_password("s3cret-pass")
        admin_user.can_access_admin = True
        admin_user.save()

    test_client = TestClient(app)
    login = test_client.post(
        "/api/admin/login", json={"username": "admin", "password": "s3cret-pass"}
    )
    assert login.status_code == 200
    return test_client


@pytest.fixture
def seeded(client):
    """Seed sample data."""
    with session_scope():
        ApiAuthor.objects.create(name="Alice", email="alice@example.com")
        ApiAuthor.objects.create(name="Bob", email="bob@example.com")
        for i in range(5):
            ApiBook.objects.create(
                title=f"Book {i}",
                status="published" if i % 2 == 0 else "draft",
                pages=100 + i,
            )


# ----------------------------------------------------------------------
# Schema
# ----------------------------------------------------------------------


def test_schema_lists_models(client):
    resp = client.get("/api/admin/schema")
    assert resp.status_code == 200
    resources = {m["resource"] for m in resp.json()["models"]}
    assert "apiauthor" in resources
    assert "apibook" in resources


def test_schema_includes_field_metadata(client):
    resp = client.get("/api/admin/schema")
    book = next(m for m in resp.json()["models"] if m["resource"] == "apibook")
    status_field = next(f for f in book["fields"] if f["name"] == "status")
    assert status_field["choices"] == [
        {"value": "draft", "label": "Draft"},
        {"value": "published", "label": "Published"},
    ]
    assert book["permissions"]["create"] is True
    assert book["listDisplay"] == ["title", "status", "pages"]


def test_schema_has_no_total(client):
    """Row counts live on /counts, not the (static) schema response."""
    resp = client.get("/api/admin/schema")
    for model in resp.json()["models"]:
        assert "total" not in model


def test_counts_endpoint_returns_per_model_counts(client, seeded):
    """One /counts call returns every model's row count (single query)."""
    resp = client.get("/api/admin/counts")
    assert resp.status_code == 200
    counts = resp.json()["counts"]
    assert counts["apibook"] == 5
    assert counts["apiauthor"] == 2


def test_counts_respects_custom_queryset_scope(client, seeded, monkeypatch):
    """Regression: /counts used to COUNT(*) the raw table for every model,
    ignoring a custom, row-filtering get_queryset() override — so its total
    could exceed (or otherwise not match) what /{resource} actually lists."""

    def published_only(self, request=None):
        return ApiBook.objects.filter(status="published")

    monkeypatch.setattr(ApiBookAdmin, "get_queryset", published_only)

    resp = client.get("/api/admin/counts")
    assert resp.status_code == 200
    # seeded() creates 5 books, alternating status; i=0,2,4 are "published".
    assert resp.json()["counts"]["apibook"] == 3


# ----------------------------------------------------------------------
# List
# ----------------------------------------------------------------------


def test_list_empty(client):
    resp = client.get("/api/admin/apibook")
    assert resp.status_code == 200
    assert resp.json() == {"data": [], "total": 0, "page": 1, "perPage": 25}


def test_list_with_data(client, seeded):
    resp = client.get("/api/admin/apibook")
    data = resp.json()
    assert data["total"] == 5
    assert len(data["data"]) == 5
    assert all("id" in row for row in data["data"])


def test_list_pagination(client, seeded):
    resp = client.get("/api/admin/apibook?page=2&perPage=2")
    data = resp.json()
    assert data["total"] == 5
    assert len(data["data"]) == 2
    assert data["page"] == 2


def test_list_search(client, seeded):
    resp = client.get("/api/admin/apibook?q=Book 3")
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["title"] == "Book 3"


def test_list_filter_by_field(client, seeded):
    resp = client.get("/api/admin/apibook?status=draft")
    data = resp.json()
    assert data["total"] == 2
    assert all(row["status"] == "draft" for row in data["data"])


def test_list_sorting(client, seeded):
    resp = client.get("/api/admin/apibook?sortField=pages&sortOrder=DESC")
    pages = [row["pages"] for row in resp.json()["data"]]
    assert pages == sorted(pages, reverse=True)


def test_list_unknown_resource_404(client):
    resp = client.get("/api/admin/nonexistent")
    assert resp.status_code == 404


# ----------------------------------------------------------------------
# Retrieve
# ----------------------------------------------------------------------


def test_get_one(client, seeded):
    with session_scope():
        book_id = ApiBook.objects.first().id
    resp = client.get(f"/api/admin/apibook/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == book_id


def test_get_one_404(client, seeded):
    resp = client.get("/api/admin/apibook/99999")
    assert resp.status_code == 404


# ----------------------------------------------------------------------
# Create
# ----------------------------------------------------------------------


def test_create(client):
    resp = client.post(
        "/api/admin/apiauthor",
        json={"name": "Charlie", "email": "charlie@example.com"},
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Charlie"
    assert data["id"] is not None


def test_create_applies_defaults(client):
    resp = client.post("/api/admin/apibook", json={"title": "New Book"})
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["status"] == "draft"
    assert data["pages"] == 0
    assert data["is_active"] is True


def test_create_validation_error_422(client):
    resp = client.post("/api/admin/apiauthor", json={"name": "X", "email": "not-an-email"})
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert "email" in detail["errors"]


def test_create_ignores_unknown_fields(client):
    resp = client.post(
        "/api/admin/apibook",
        json={"title": "T", "hacker_field": "pwned"},
    )
    assert resp.status_code == 201


# ----------------------------------------------------------------------
# Update
# ----------------------------------------------------------------------


def test_update(client, seeded):
    with session_scope():
        book_id = ApiBook.objects.filter(title="Book 0").first().id
    resp = client.put(f"/api/admin/apibook/{book_id}", json={"pages": 500})
    assert resp.status_code == 200
    assert resp.json()["data"]["pages"] == 500
    assert resp.json()["data"]["title"] == "Book 0"


def test_update_validation_error_422(client, seeded):
    with session_scope():
        author_id = ApiAuthor.objects.first().id
    resp = client.put(f"/api/admin/apiauthor/{author_id}", json={"email": "bad"})
    assert resp.status_code == 422


def test_update_404(client, seeded):
    resp = client.put("/api/admin/apibook/99999", json={"pages": 1})
    assert resp.status_code == 404


# ----------------------------------------------------------------------
# Delete
# ----------------------------------------------------------------------


def test_delete(client, seeded):
    with session_scope():
        book_id = ApiBook.objects.first().id
    resp = client.delete(f"/api/admin/apibook/{book_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == book_id

    resp = client.get(f"/api/admin/apibook/{book_id}")
    assert resp.status_code == 404


def test_delete_404(client, seeded):
    resp = client.delete("/api/admin/apibook/99999")
    assert resp.status_code == 404


def test_bulk_delete(client, seeded):
    with session_scope():
        ids = [b.id for b in ApiBook.objects.all()[:3]]
    query = "&".join(f"ids={i}" for i in ids)
    resp = client.delete(f"/api/admin/apibook?{query}")
    assert resp.status_code == 200
    assert resp.json()["data"] == ids

    resp = client.get("/api/admin/apibook")
    assert resp.json()["total"] == 2


# ----------------------------------------------------------------------
# Audit log (shared by the admin API and the token-authenticated REST API
# — see tests/test_rest_api.py for the token-auth side of this)
# ----------------------------------------------------------------------


def test_create_writes_audit_log_attributed_to_admin_user(client):
    resp = client.post(
        "/api/admin/apiauthor", json={"name": "Dana", "email": "dana@example.com"}
    )
    author_id = resp.json()["data"]["id"]

    with session_scope():
        entry = AuditLog.objects.get(action="create", model_name="ApiAuthor")
        assert entry.username == "admin"
        assert entry.source == "admin"
        assert entry.object_id == str(author_id)
        assert entry.changes["fields"]["name"] == "Dana"


def test_update_writes_audit_log_diff_only_changed_fields(client, seeded):
    with session_scope():
        book_id = ApiBook.objects.filter(title="Book 0").first().id

    client.put(f"/api/admin/apibook/{book_id}", json={"pages": 777})

    with session_scope():
        entry = AuditLog.objects.get(action="update", model_name="ApiBook")
        assert entry.changes["pages"] == {"old": 100, "new": 777}
        assert "title" not in entry.changes


def test_delete_writes_audit_log_with_pre_delete_snapshot(client, seeded):
    with session_scope():
        book_id = ApiBook.objects.filter(title="Book 0").first().id

    client.delete(f"/api/admin/apibook/{book_id}")

    with session_scope():
        entry = AuditLog.objects.get(action="delete", model_name="ApiBook")
        assert entry.object_id == str(book_id)
        assert entry.changes["fields"]["title"] == "Book 0"


def test_bulk_delete_writes_one_audit_entry_per_object(client, seeded):
    with session_scope():
        ids = [b.id for b in ApiBook.objects.all()[:2]]

    query = "&".join(f"ids={i}" for i in ids)
    client.delete(f"/api/admin/apibook?{query}")

    with session_scope():
        entries = list(AuditLog.objects.filter(action="delete", model_name="ApiBook"))
        assert {e.object_id for e in entries} == {str(i) for i in ids}
