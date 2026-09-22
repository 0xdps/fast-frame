from __future__ import annotations

import argparse

import pytest

from fastframe.cli import manage


def test_test_command_passes_bare_flags_without_double_dash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression test: `manage.py test -v` used to fail with
    'unrecognized arguments: -v' because argparse subparsers can't reliably
    pass dash-prefixed tokens through nargs=REMAINDER. It should now work
    without requiring `--`.
    """
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        manage.testcmd, "execute", lambda args: captured.setdefault("args", args)
    )

    manage.execute_from_command_line(["manage.py", "test", "-v"])

    assert captured["args"].pytest_args == ["-v"]


def test_test_command_still_strips_leading_double_dash(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        manage.testcmd, "execute", lambda args: captured.setdefault("args", args)
    )

    manage.execute_from_command_line(["manage.py", "test", "--", "-k", "todo"])

    assert captured["args"].pytest_args == ["-k", "todo"]


def test_test_command_with_no_args(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setattr(
        manage.testcmd, "execute", lambda args: captured.setdefault("args", args)
    )

    manage.execute_from_command_line(["manage.py", "test"])

    assert captured["args"].pytest_args == []


def test_version_flag(capsys: pytest.CaptureFixture) -> None:
    from fastframe.__version__ import __version__

    with pytest.raises(SystemExit) as exc_info:
        manage.execute_from_command_line(["manage.py", "--version"])
    assert exc_info.value.code == 0

    out = capsys.readouterr().out
    assert __version__ in out


def test_settings_error_is_reported_cleanly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    """A misconfigured FASTFRAME_SETTINGS_MODULE should print a clean
    one-line error and exit 1, not a raw traceback.
    """
    from fastframe.core.settings import SettingsError

    def _raise(args: argparse.Namespace) -> None:
        raise SettingsError("Settings module not configured.")

    monkeypatch.setattr(manage.check, "execute", _raise)

    with pytest.raises(SystemExit) as exc_info:
        manage.execute_from_command_line(["manage.py", "check"])
    assert exc_info.value.code == 1

    err = capsys.readouterr().err
    assert "Settings module not configured." in err
