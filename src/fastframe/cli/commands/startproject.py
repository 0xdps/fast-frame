from __future__ import annotations

import argparse
import sys
from pathlib import Path


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("name", help="Project name and default directory name")
    parser.add_argument(
        "directory",
        nargs="?",
        help="Optional destination directory (defaults to project name)",
    )


def execute(args: argparse.Namespace) -> None:
    run_startproject(args.name, args.directory)


def run_startproject(name: str, directory: str | None = None) -> Path:
    from fastframe.cli.scaffold import ScaffoldError, create_project, validate_name

    project_slug = name.replace("-", "_")
    try:
        validate_name(project_slug)
        if directory:
            destination = Path(directory).resolve()
        else:
            destination = (Path.cwd() / name).resolve()
        create_project(destination, project_slug)
    except ScaffoldError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Project '{project_slug}' created at {destination}")
    print(f"  cd {destination.name}")
    print("  pip install fastframe  # or pip install -e /path/to/ff")
    print("  python manage.py migrate")
    print("  python manage.py runserver")
    return destination
