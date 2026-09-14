from __future__ import annotations

from fastapi.testclient import TestClient


def test_user_objects_crud(miniproject_env) -> None:
    from users.models import User

    from fastframe.core.bootstrap import bootstrap
    from fastframe.db.session import session_scope

    bootstrap(None)

    with session_scope():
        assert User.objects.count() == 0
        user = User.objects.create(email="dev@example.com", is_active=True)
        assert user.id is not None

    with session_scope():
        assert User.objects.count() == 1
        found = User.objects.get(email="dev@example.com")
        assert found.is_active is True
        assert User.objects.filter(is_active=True)[0].email == "dev@example.com"


def test_get_user_endpoint(miniproject_env) -> None:
    from config.asgi import application
    from users.models import User

    from fastframe.core.bootstrap import bootstrap
    from fastframe.db.session import session_scope

    bootstrap(None)

    with session_scope():
        User.objects.create(email="api@example.com")

    client = TestClient(application)
    response = client.get("/users/1")
    assert response.status_code == 200
    assert response.json() == {
        "id": 1,
        "email": "api@example.com",
        "is_active": True,
    }

    missing = client.get("/users/999")
    assert missing.status_code == 404
