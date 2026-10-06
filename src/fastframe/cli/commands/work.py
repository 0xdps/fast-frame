"""Start a Celery worker."""

from __future__ import annotations

import argparse


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--loglevel", default="info", help="Celery log level (default: info)")


def execute(args: argparse.Namespace) -> None:
    from fastframe.tasks.runtime import start

    start("worker", args.loglevel)
