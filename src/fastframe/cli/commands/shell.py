from __future__ import annotations

import argparse

from fastframe.core.bootstrap import bootstrap
from fastframe.db.init import import_app_models
from fastframe.db.session import begin_session, end_session
from fastframe.shell.context import ShellStartupError, build_shell_namespace
from fastframe.shell.interfaces import ShellInterfaceError, resolve_shell_interface, run_shell


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-i",
        "--interface",
        choices=["auto", "ptpython", "ipython", "python"],
        default=None,
        help=(
            "REPL to use. Overrides the SHELL_INTERFACE setting for this run "
            "(default: SHELL_INTERFACE, or 'auto' if unset — tries ptpython, "
            "then IPython, then the standard library REPL)."
        ),
    )


def execute(args: argparse.Namespace) -> None:
    registry = bootstrap(None)
    import_app_models(registry)

    session, token = begin_session(None)
    banner = (
        "FastFrame shell (Python REPL)\n"
        "Models and SHELL_IMPORTS / shell_startup.py are loaded.\n"
        "Type exit() or Ctrl-D to quit."
    )
    try:
        local_namespace = build_shell_namespace(registry, session)
    except ShellStartupError as exc:
        end_session(session, token, commit=False)
        raise SystemExit(str(exc)) from exc

    interface_setting = args.interface or getattr(registry.settings, "SHELL_INTERFACE", "auto")
    try:
        interface = resolve_shell_interface(interface_setting)
    except ShellInterfaceError as exc:
        end_session(session, token, commit=False)
        raise SystemExit(str(exc)) from exc

    try:
        run_shell(interface, local_namespace, banner)
        end_session(session, token, commit=True)
    except SystemExit:
        end_session(session, token, commit=True)
        raise
    except KeyboardInterrupt:
        end_session(session, token, commit=False)
    except Exception:
        end_session(session, token, commit=False)
        raise
