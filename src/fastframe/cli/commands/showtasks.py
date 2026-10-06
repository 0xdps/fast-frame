"""List Beat schedules and the tasks a worker will run."""

from __future__ import annotations

import argparse


def add_arguments(parser: argparse.ArgumentParser) -> None:
    pass


def execute(args: argparse.Namespace) -> None:
    from fastframe.tasks.listing import show_tasks

    show_tasks()
