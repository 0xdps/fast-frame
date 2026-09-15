from __future__ import annotations


def test_model_repr(miniproject_env) -> None:
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        user = User.objects.create(email="repr@example.com", is_active=True)
        repr_str = repr(user)
        assert "User" in repr_str
        assert "email='repr@example.com'" in repr_str
        assert "is_active=True" in repr_str
