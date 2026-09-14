from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="fastframe", description="FastFrame global CLI")
    subparsers = parser.add_subparsers(dest="command")

    startproject = subparsers.add_parser("startproject", help="Create a new FastFrame project")
    startproject.add_argument("name", help="Project name (also used as default directory name)")
    startproject.add_argument(
        "directory",
        nargs="?",
        help="Optional destination directory",
    )

    subparsers.add_parser("version", help="Show version")

    if not argv:
        parser.print_help()
        return

    args = parser.parse_args(argv)

    if args.command == "version":
        from fastframe.__version__ import __version__

        print(__version__)
        return
    if args.command == "startproject":
        from fastframe.cli.commands.startproject import run_startproject

        run_startproject(args.name, getattr(args, "directory", None))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
