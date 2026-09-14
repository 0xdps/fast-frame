from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_migrate_applies_users_table(miniproject_env, miniproject_path: Path) -> None:
    from users.models import User

    from fastframe.db.session import session_scope

    with session_scope():
        User.objects.create(email="migrated@example.com")
        assert User.objects.count() == 1


def test_manage_py_migrate(miniproject_env, miniproject_path: Path) -> None:
    manage = miniproject_path / "manage.py"
    result = subprocess.run(
        [sys.executable, str(manage), "migrate"],
        cwd=miniproject_path,
        capture_output=True,
        text=True,
        check=False,
        env={
            **dict(__import__("os").environ),
            "FASTFRAME_SETTINGS_MODULE": "config.settings",
            "DATABASE_URL": "sqlite:///:memory:",
        },
    )
    assert result.returncode == 0, result.stderr
