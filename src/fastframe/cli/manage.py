from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from fastframe.cli.commands import (
    check,
    makemigrations,
    migrate,
    runserver,
    shell,
    startapp,
    testcmd,
)

COMMANDS = {
    "runserver": runserver,
    "check": check,
    "makemigrations": makemigrations,
    "migrate": migrate,
    "shell": shell,
    "test": testcmd,
    "startapp": startapp,
}


def execute_from_command_line(argv: Sequence[str] | None = None) -> None:
    argv = list(argv if argv is not None else sys.argv)
    prog = argv[0] if argv else "manage.py"
    parser = argparse.ArgumentParser(prog=prog, description="FastFrame management utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, module in COMMANDS.items():
        sub = subparsers.add_parser(name, help=name)
        module.add_arguments(sub)
        sub.set_defaults(_command_module=module)

    args = parser.parse_args(argv[1:])
    module = args._command_module
    module.execute(args)
