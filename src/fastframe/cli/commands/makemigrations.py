from __future__ import annotations

import argparse


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-n",
        "--name",
        default="auto",
        help="Short description for the generated migration",
    )
    parser.add_argument(
        "app_labels",
        nargs="*",
        help="Only write migrations for these apps (default: every app that changed)",
    )


def execute(args: argparse.Namespace) -> None:
    from fastframe.migrations.runner import makemigrations

    makemigrations(message=args.name, app_labels=list(args.app_labels))
