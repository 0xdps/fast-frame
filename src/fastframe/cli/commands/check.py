from __future__ import annotations

import argparse


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--database",
        action="store_true",
        help="Also run database checks (connectivity, pending migrations).",
    )


def execute(args: argparse.Namespace) -> None:
    from fastframe.core.bootstrap import bootstrap
    from fastframe.core.checks import is_serious, run_checks

    registry = bootstrap(None)
    include_database = getattr(args, "database", False)
    messages = run_checks(registry, include_database=include_database)

    if not messages:
        print("System check identified no issues (0 silenced).")
        return

    for message in messages:
        print(f"{message.level_name}: {message}")

    noun = "issue" if len(messages) == 1 else "issues"
    print(f"\nSystem check identified {len(messages)} {noun} (0 silenced).")

    if is_serious(messages):
        raise SystemExit(1)
