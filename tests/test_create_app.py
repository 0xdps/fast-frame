"""create_app honors admin and OpenAPI settings."""

from fastapi.testclient import TestClient

from fastframe.core.bootstrap import reset_bootstrap


def _reload(monkeypatch, module: str) -> None:
    monkeypatch.setenv("FASTFRAME_SETTINGS_MODULE", module)
    reset_bootstrap()
    from fastframe.conf import settings

    settings.reload()


def test_openapi_and_admin_can_be_disabled(monkeypatch):
    _reload(monkeypatch, "tests.fixtures.openapi_off_settings")
    from fastframe.core.app import create_app

    app = create_app()
    assert app.openapi_url is None
    assert app.docs_url is None
    assert app.redoc_url is None
    paths = [getattr(route, "path", "") for route in app.routes]
    assert not any(path.startswith("/api/admin") or path.startswith("/admin") for path in paths)


def test_static_admin_and_docs_are_mounted(monkeypatch):
    # ":memory:" (not just "sqlite://") is required for StaticPool to kick
    # in (see fastframe.db.engine.get_engine) — this test now needs the User
    # table to persist across connections to log in.
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    _reload(monkeypatch, "tests.fixtures.test_settings")
    from fastframe.contrib.auth.models import User
    from fastframe.core.app import create_app
    from fastframe.db.engine import get_engine
    from fastframe.db.session import session_scope
    from fastframe.models import Model

    app = create_app()
    assert app.docs_url == "/docs"
    client = TestClient(app)

    # Admin is always auth-gated: unauthenticated requests get a login page.
    page = client.get("/admin/")
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    schema = client.get("/api/admin/schema")
    assert schema.status_code == 401

    Model.metadata.create_all(bind=get_engine())
    with session_scope():
        user = User(username="admin", email="admin@example.com", password="")
        user.set_password("s3cret-pass")
        user.can_access_admin = True
        user.save()
    login = client.post("/api/admin/login", json={"username": "admin", "password": "s3cret-pass"})
    assert login.status_code == 200

    schema = client.get("/api/admin/schema")
    assert schema.status_code == 200
    assert "models" in schema.json()
