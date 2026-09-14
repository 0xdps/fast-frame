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
        help="Optional app labels (ignored in v0.1; migrations autogenerate all models)",
    )


def execute(args: argparse.Namespace) -> None:
    from fastframe.migrations.runner import makemigrations

    makemigrations(message=args.name)
