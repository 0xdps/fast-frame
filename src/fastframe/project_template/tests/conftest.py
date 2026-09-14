from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def project_env(monkeypatch: pytest.MonkeyPatch) -> Path:
    path_str = str(PROJECT_ROOT)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.setenv("FASTFRAME_SETTINGS_MODULE", "config.settings")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from fastframe.core.bootstrap import bootstrap, reset_bootstrap
    from fastframe.migrations.runner import migrate

    reset_bootstrap()
    bootstrap(None)
    migrate()
    return PROJECT_ROOT
