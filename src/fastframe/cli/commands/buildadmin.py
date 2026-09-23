"""Build the React admin and copy the compiled files into a static directory."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path


def add_arguments(parser: ArgumentParser) -> None:
    """Add command line arguments."""
    parser.add_argument(
        "--source",
        default=None,
        help="React admin project to build (default: the admin shipped with FastFrame)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Directory for compiled files (default: fastframe/admin/static)",
    )
    parser.add_argument(
        "--base",
        default=None,
        help="Vite base path, including trailing slash (default: <ADMIN_PREFIX>/)",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="Value for VITE_API_URL (default: ADMIN_API_PREFIX)",
    )


def _package_admin_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "admin"


def execute(args: object) -> None:
    """Install dependencies if needed, build, and copy dist/ to the output dir."""
    from fastframe.core.bootstrap import bootstrap

    bootstrap()
    from fastframe.conf import settings

    source_arg = getattr(args, "source", None)
    output_arg = getattr(args, "output", None)
    source = Path(source_arg) if source_arg else _package_admin_dir() / "templates" / "admin-ui"
    output = Path(output_arg) if output_arg else _package_admin_dir() / "static"

    if not (source / "package.json").is_file():
        print(f"Error: {source} is not a React admin project (no package.json).", file=sys.stderr)
        raise SystemExit(1)

    prefix = str(getattr(settings, "ADMIN_PREFIX", "/admin")).rstrip("/") or "/admin"
    base = getattr(args, "base", None) or f"{prefix}/"
    if not base.endswith("/"):
        base = f"{base}/"
    api_url = getattr(args, "api_url", None) or str(
        getattr(settings, "ADMIN_API_PREFIX", "/api/admin")
    )

    env = os.environ.copy()
    env["VITE_BASE"] = base
    env["VITE_API_URL"] = api_url

    npm = shutil.which("npm")
    if npm is None:
        print("Error: npm is not on PATH. Install Node.js to build the admin.", file=sys.stderr)
        raise SystemExit(1)

    print(f"Building admin from {source}")
    print(f"  base:    {base}")
    print(f"  api url: {api_url}")
    print("Installing npm dependencies...")
    subprocess.run([npm, "install"], cwd=source, env=env, check=True)

    print("Running npm run build...")
    subprocess.run([npm, "run", "build"], cwd=source, env=env, check=True)

    dist = source / "dist"
    if not (dist / "index.html").is_file():
        print(f"Error: build did not produce {dist / 'index.html'}.", file=sys.stderr)
        raise SystemExit(1)

    output.mkdir(parents=True, exist_ok=True)
    for child in output.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in dist.iterdir():
        destination = output / child.name
        if child.is_dir():
            shutil.copytree(child, destination)
        else:
            shutil.copy2(child, destination)

    print(f"Compiled admin written to {output}")
