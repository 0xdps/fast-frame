from __future__ import annotations

import argparse
import code

from fastframe.core.bootstrap import bootstrap
from fastframe.db.init import import_app_models
from fastframe.db.session import begin_session, end_session
from fastframe.shell.context import ShellStartupError, build_shell_namespace


def add_arguments(parser: argparse.ArgumentParser) -> None:
    pass


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

    try:
        code.interact(banner=banner, local=local_namespace)
        end_session(session, token, commit=True)
    except SystemExit:
        end_session(session, token, commit=True)
        raise
    except KeyboardInterrupt:
        end_session(session, token, commit=False)
    except Exception:
        end_session(session, token, commit=False)
        raise
