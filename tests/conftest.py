from __future__ import annotations

import sys
from pathlib import Path

import pytest

MINIPROJECT_ROOT = Path(__file__).resolve().parent / "fixtures" / "miniproject"


@pytest.fixture(autouse=True)
def _reset_rate_limiters():
    """The login rate limiter is a process-global singleton (it has to be,
    to actually rate-limit across requests) — reset it before every test so
    one test's failed-login attempts never leak into another's as a bogus
    429, regardless of run order.
    """
    from fastframe.core.ratelimit import reset_rate_limiters

    reset_rate_limiters()
    yield
    reset_rate_limiters()


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
