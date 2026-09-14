from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from fastframe.cli.commands.startproject import run_startproject
from fastframe.cli.scaffold import ScaffoldError, validate_name


def test_validate_name_rejects_invalid() -> None:
    with pytest.raises(ScaffoldError):
        validate_name("1bad")


def test_startproject_creates_layout(tmp_path: Path) -> None:
    dest = tmp_path / "demo"
    run_startproject("demo", str(dest))
    assert (dest / "manage.py").is_file()
    assert (dest / "config" / "settings.py").is_file()
    assert (dest / "health" / "urls.py").is_file()
    assert (dest / "tests" / "test_health.py").is_file()
    settings = (dest / "config" / "settings.py").read_text(encoding="utf-8")
    assert "demo" in settings.lower() or "Demo" in settings


def test_startapp_scaffold_and_wiring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dest = tmp_path / "demo"
    run_startproject("demo", str(dest))
    monkeypatch.chdir(dest)
    sys.path.insert(0, str(dest))

    import argparse

    from fastframe.cli.commands.startapp import execute

    execute(argparse.Namespace(name="billing"))
    assert (dest / "billing" / "models.py").is_file()
    settings = (dest / "config" / "settings.py").read_text(encoding="utf-8")
    assert '"billing"' in settings
    urls = (dest / "config" / "urls.py").read_text(encoding="utf-8")
    assert "billing_router" in urls


def test_shell_invokes_interact(miniproject_env) -> None:
    import argparse

    from fastframe.cli.commands import shell

    with patch("code.interact") as interact:
        shell.execute(argparse.Namespace(plain=True))
        interact.assert_called_once()


def test_manage_py_test_in_generated_project(tmp_path: Path) -> None:
    dest = tmp_path / "demo"
    run_startproject("demo", str(dest))
    env = {
        **dict(__import__("os").environ),
        "PYTHONPATH": str(dest),
        "FASTFRAME_SETTINGS_MODULE": "config.settings",
        "DATABASE_URL": "sqlite:///:memory:",
    }
    result = subprocess.run(
        [sys.executable, "manage.py", "test"],
        cwd=dest,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
