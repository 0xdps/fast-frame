from __future__ import annotations

import sys
from pathlib import Path

import pytest

MINIPROJECT_ROOT = Path(__file__).resolve().parent / "fixtures" / "miniproject"


@pytest.fixture(scope="session")
def miniproject_path() -> Path:
    return MINIPROJECT_ROOT


@pytest.fixture
def miniproject_env(miniproject_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put the fixture project on sys.path and configure settings."""
    path_str = str(miniproject_path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    monkeypatch.setenv("FASTFRAME_SETTINGS_MODULE", "config.settings")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.chdir(miniproject_path)

    from fastframe.core.bootstrap import bootstrap, reset_bootstrap
    from fastframe.migrations.runner import migrate

    reset_bootstrap()
    bootstrap(None)
    migrate()

    return miniproject_path
