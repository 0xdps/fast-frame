"""App management commands discovered from INSTALLED_APPS."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from fastframe.cli import manage


@contextmanager
def _app_command(root: Path, app: str, name: str, source: str) -> Iterator[None]:
    app_dir = root / app
    app_existed = app_dir.exists()
    management = app_dir / "management"
    commands = management / "commands"
    commands.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    for directory in (management, commands):
        init = directory / "__init__.py"
        if not init.exists():
            init.write_text("")
            created.append(init)
    module_path = commands / f"{name}.py"
    module_path.write_text(source)
    created.append(module_path)
    importlib.invalidate_caches()
    try:
        yield
    finally:
        for path in reversed(created):
            path.unlink(missing_ok=True)
        for directory in (commands, management):
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
        if not app_existed and app_dir.exists() and not any(app_dir.iterdir()):
            app_dir.rmdir()
        prefix = f"{app}.management"
        for key in list(sys.modules):
            if key == prefix or key.startswith(prefix + "."):
                del sys.modules[key]
        importlib.invalidate_caches()


def test_app_command_runs_with_its_arguments(miniproject_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = '''
"""Say hello."""

def add_arguments(parser):
    parser.add_argument("name")

def execute(args):
    print(f"hello {args.name}")
'''
    with _app_command(miniproject_env, "users", "greet", source):
        manage.execute_from_command_line(["manage.py", "greet", "ada"])
    assert capsys.readouterr().out.strip() == "hello ada"


def test_app_command_help_uses_the_docstring(miniproject_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = '''
"""Say hello."""

def execute(args):
    print("hello")
'''
    with _app_command(miniproject_env, "users", "greet", source):
        with pytest.raises(SystemExit) as exc_info:
            manage.execute_from_command_line(["manage.py", "--help"])
    assert exc_info.value.code == 0
    assert "Say hello." in capsys.readouterr().out


def test_uninstalled_app_command_is_not_registered(miniproject_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = "def execute(args):\n    print('nope')\n"
    with _app_command(miniproject_env, "extras", "extra", source):
        with pytest.raises(SystemExit) as exc_info:
            manage.execute_from_command_line(["manage.py", "extra"])
    assert exc_info.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_builtin_command_name_is_rejected(miniproject_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = "def execute(args):\n    print('shadow')\n"
    with _app_command(miniproject_env, "users", "check", source):
        with pytest.raises(SystemExit) as exc_info:
            manage.execute_from_command_line(["manage.py", "check"])
    assert exc_info.value.code == 1
    assert "already a built-in command" in capsys.readouterr().err


def test_duplicate_command_names_are_rejected(miniproject_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = "def execute(args):\n    pass\n"
    with (
        _app_command(miniproject_env, "users", "greet", source),
        _app_command(miniproject_env, "posts", "greet", source),
    ):
        with pytest.raises(SystemExit) as exc_info:
            manage.execute_from_command_line(["manage.py", "greet"])
    assert exc_info.value.code == 1
    err = capsys.readouterr().err
    assert "users" in err
    assert "posts" in err


def test_command_module_must_define_execute(miniproject_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    with _app_command(miniproject_env, "users", "greet", "ADD = 1\n"):
        with pytest.raises(SystemExit) as exc_info:
            manage.execute_from_command_line(["manage.py", "greet"])
    assert exc_info.value.code == 1
    assert "must define execute(args)" in capsys.readouterr().err


def test_missing_installed_app_is_reported(miniproject_env: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import config.settings as project_settings

    original = list(project_settings.INSTALLED_APPS)
    project_settings.INSTALLED_APPS = [*original, "not_an_app"]
    try:
        with pytest.raises(SystemExit) as exc_info:
            manage.execute_from_command_line(["manage.py", "check"])
    finally:
        project_settings.INSTALLED_APPS = original
    assert exc_info.value.code == 1
    assert 'Cannot import installed app "not_an_app"' in capsys.readouterr().err


def test_discover_without_settings_leaves_builtins(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastframe.core.settings import SettingsError

    monkeypatch.delenv("FASTFRAME_SETTINGS_MODULE", raising=False)
    with pytest.raises(SettingsError):
        from fastframe.cli.discovery import discover_app_commands

        discover_app_commands()

    with pytest.raises(SystemExit) as exc_info:
        manage.execute_from_command_line(["manage.py", "--version"])
    assert exc_info.value.code == 0
