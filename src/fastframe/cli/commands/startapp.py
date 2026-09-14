from __future__ import annotations

import argparse
import sys
from pathlib import Path


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("name", help="App module name (e.g. users)")


def execute(args: argparse.Namespace) -> None:
    from fastframe.cli.scaffold import (
        ScaffoldError,
        add_installed_app,
        add_router_to_urls,
        create_app,
        validate_name,
    )

    try:
        app_name = validate_name(args.name)
        app_dir = Path.cwd() / app_name
        create_app(app_dir, app_name)
        add_installed_app(Path.cwd() / "config" / "settings.py", app_name)
        add_router_to_urls(Path.cwd() / "config" / "urls.py", app_name)
    except ScaffoldError as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"App '{app_name}' created.")
    print(f"  1. Define models in {app_name}/models.py")
    print("  2. python manage.py makemigrations")
    print("  3. python manage.py migrate")
