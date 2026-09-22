from __future__ import annotations

import argparse


def add_arguments(parser: argparse.ArgumentParser) -> None:
    pass


def execute(args: argparse.Namespace) -> None:
    from fastframe.migrations.runner import showmigrations

    showmigrations()
