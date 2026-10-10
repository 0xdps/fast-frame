"""Tests for REPL interface selection (src/fastframe/shell/interfaces.py)
and its wiring into `manage.py shell` (src/fastframe/cli/commands/shell.py).

Availability of ptpython/IPython is monkeypatched rather than relying on
whether those optional packages happen to be installed in the test
environment, so these pass whether or not `fast-frame[shell]` is installed.
"""

from __future__ import annotations

import pytest

from fastframe.shell import interfaces


def test_resolve_python_is_always_available() -> None:
    assert interfaces.resolve_shell_interface("python") == "python"


def test_resolve_unknown_interface_raises() -> None:
    with pytest.raises(interfaces.ShellInterfaceError, match="Unknown SHELL_INTERFACE"):
        interfaces.resolve_shell_interface("not-a-real-interface")


def test_resolve_specific_interface_available(monkeypatch) -> None:
    monkeypatch.setitem(interfaces._AVAILABILITY, "ptpython", lambda: True)
    assert interfaces.resolve_shell_interface("ptpython") == "ptpython"


def test_resolve_specific_interface_unavailable_raises(monkeypatch) -> None:
    monkeypatch.setitem(interfaces._AVAILABILITY, "ptpython", lambda: False)
    with pytest.raises(interfaces.ShellInterfaceError, match="ptpython"):
        interfaces.resolve_shell_interface("ptpython")


def test_auto_prefers_ptpython_then_ipython_then_python(monkeypatch) -> None:
    monkeypatch.setitem(interfaces._AVAILABILITY, "ptpython", lambda: True)
    monkeypatch.setitem(interfaces._AVAILABILITY, "ipython", lambda: True)
    assert interfaces.resolve_shell_interface("auto") == "ptpython"

    monkeypatch.setitem(interfaces._AVAILABILITY, "ptpython", lambda: False)
    assert interfaces.resolve_shell_interface("auto") == "ipython"

    monkeypatch.setitem(interfaces._AVAILABILITY, "ipython", lambda: False)
    assert interfaces.resolve_shell_interface("auto") == "python"


def test_run_shell_python_calls_code_interact(monkeypatch) -> None:
    calls = {}

    def fake_interact(banner: str, local: dict) -> None:
        calls["banner"] = banner
        calls["local"] = local

    monkeypatch.setattr("code.interact", fake_interact)
    interfaces.run_shell("python", {"x": 1}, "hello banner")

    assert calls == {"banner": "hello banner", "local": {"x": 1}}


def test_run_shell_ipython_disables_blank_line_before_prompt(monkeypatch) -> None:
    """IPython's `separate_in` defaults to "\\n", printing a blank line
    before every `In [n]:` prompt — denser terminal REPLs (and FastFrame's
    own stdlib/ptpython interfaces) don't do this, so it's turned off.
    """
    import types

    calls = {}
    fake_ipython = types.SimpleNamespace(embed=lambda **kwargs: calls.update(kwargs))
    monkeypatch.setitem(__import__("sys").modules, "IPython", fake_ipython)

    interfaces.run_shell("ipython", {"x": 1}, "hello banner")

    assert calls["separate_in"] == ""
    assert calls["user_ns"] == {"x": 1}
    assert calls["header"] == "hello banner"


def test_run_shell_unknown_interface_raises_key_error() -> None:
    # run_shell expects an already-resolved name (not "auto") — an unknown
    # name is a programming error, not a user-facing ShellInterfaceError.
    with pytest.raises(KeyError):
        interfaces.run_shell("not-a-real-interface", {}, "")


# ----------------------------------------------------------------------
# CLI wiring (fastframe.cli.commands.shell)
# ----------------------------------------------------------------------


def test_shell_cli_interface_flag_overrides_setting(miniproject_env, monkeypatch) -> None:
    from argparse import Namespace

    from fastframe.cli.commands import shell as shell_cmd

    calls = {}
    monkeypatch.setattr(shell_cmd, "run_shell", lambda interface, namespace, banner: calls.update(interface=interface))

    shell_cmd.execute(Namespace(interface="python"))

    assert calls["interface"] == "python"


def test_shell_cli_falls_back_to_setting_then_auto(miniproject_env, monkeypatch) -> None:
    from argparse import Namespace

    from fastframe.cli.commands import shell as shell_cmd

    calls = {}
    monkeypatch.setattr(shell_cmd, "run_shell", lambda interface, namespace, banner: calls.update(interface=interface))

    # No SHELL_INTERFACE set on the miniproject fixture's settings -> "auto",
    # which resolves to "python" since ptpython/IPython aren't installed
    # (or, if they are, whichever resolves first) — assert against the
    # real resolver so this doesn't hardcode an assumption either way.
    shell_cmd.execute(Namespace(interface=None))

    assert calls["interface"] == interfaces.resolve_shell_interface("auto")


def test_shell_cli_invalid_setting_raises_system_exit(miniproject_env, monkeypatch) -> None:
    from argparse import Namespace

    import config.settings as settings_module

    from fastframe.cli.commands import shell as shell_cmd

    monkeypatch.setattr(settings_module, "SHELL_INTERFACE", "not-a-real-interface", raising=False)

    with pytest.raises(SystemExit, match="Unknown SHELL_INTERFACE"):
        shell_cmd.execute(Namespace(interface=None))
