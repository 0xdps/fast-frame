from __future__ import annotations

import argparse


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "revision",
        nargs="?",
        default="head",
        help="Revision target (default: head)",
    )


def execute(args: argparse.Namespace) -> None:
    from fastframe.migrations.runner import migrate

    migrate(revision=args.revision)
