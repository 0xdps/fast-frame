from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from fastframe.__version__ import __version__
from fastframe.cli.commands import (
    check,
    dbshell,
    makemigrations,
    migrate,
    runserver,
    shell,
    showmigrations,
    startapp,
    testcmd,
)

COMMANDS = {
    "runserver": runserver,
    "check": check,
    "makemigrations": makemigrations,
    "migrate": migrate,
    "showmigrations": showmigrations,
    "dbshell": dbshell,
    "shell": shell,
    "test": testcmd,
    "startapp": startapp,
}


def execute_from_command_line(argv: Sequence[str] | None = None) -> None:
    argv = list(argv if argv is not None else sys.argv)
    prog = argv[0] if argv else "manage.py"

    # `test` forwards arbitrary flags straight through to pytest (-v, -k,
    # --pdb, ...). argparse subparsers can't reliably pass through
    # dash-prefixed tokens immediately after the subcommand name even with
    # nargs=REMAINDER on the child parser (a known argparse limitation), so
    # `manage.py test -v` used to fail with "unrecognized arguments: -v"
    # unless you wrote `manage.py test -- -v`. Handle `test` before argparse
    # ever sees the raw argv, like `git`/`npm` do for passthrough commands.
    # `--` is still accepted (and stripped) for backward compatibility.
    if len(argv) > 1 and argv[1] == "test":
        pytest_args = argv[2:]
        if pytest_args and pytest_args[0] == "--":
            pytest_args = pytest_args[1:]
        _run(testcmd, argparse.Namespace(pytest_args=pytest_args))
        return

    parser = argparse.ArgumentParser(prog=prog, description="FastFrame management utility")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, module in COMMANDS.items():
        sub = subparsers.add_parser(name, help=name)
        module.add_arguments(sub)
        sub.set_defaults(_command_module=module)

    args = parser.parse_args(argv[1:])
    module = args._command_module
    _run(module, args)


def _run(module: object, args: argparse.Namespace) -> None:
    """Run a command module's execute(), turning known configuration
    mistakes into a clean one-line error instead of a raw traceback.
    """
    from fastframe.core.settings import SettingsError

    try:
        module.execute(args)  # type: ignore[attr-defined]
    except SettingsError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
