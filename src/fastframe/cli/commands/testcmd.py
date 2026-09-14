from __future__ import annotations

import argparse
import os


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "pytest_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to pytest (e.g. manage.py test -- -k health)",
    )


def execute(args: argparse.Namespace) -> None:
    os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

    pytest_args = list(args.pytest_args)
    if pytest_args and pytest_args[0] == "--":
        pytest_args = pytest_args[1:]
    if not pytest_args:
        pytest_args = ["tests"]

    import pytest

    raise SystemExit(pytest.main(pytest_args))
