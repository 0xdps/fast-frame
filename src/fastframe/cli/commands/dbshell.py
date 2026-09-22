from __future__ import annotations

import argparse
import os


def add_arguments(parser: argparse.ArgumentParser) -> None:
    pass


def build_dbshell_command(database_url: str) -> tuple[list[str], dict[str, str]]:
    """Build the argv + extra env for the native DB client. Pure/testable —
    the actual `os.execvpe` replacement happens in `execute()`.
    """
    from sqlalchemy.engine import make_url

    url = make_url(database_url)
    driver = url.get_backend_name()
    env: dict[str, str] = {}

    if driver == "sqlite":
        db_path = url.database or ":memory:"
        return ["sqlite3", db_path], env

    if driver == "postgresql":
        argv = ["psql"]
        if url.host:
            argv += ["-h", url.host]
        if url.port:
            argv += ["-p", str(url.port)]
        if url.username:
            argv += ["-U", url.username]
        if url.password:
            env["PGPASSWORD"] = url.password
        if url.database:
            argv += [url.database]
        return argv, env

    if driver in ("mysql", "mariadb"):
        argv = ["mysql"]
        if url.host:
            argv += ["-h", url.host]
        if url.port:
            argv += ["-P", str(url.port)]
        if url.username:
            argv += ["-u", url.username]
        if url.password:
            env["MYSQL_PWD"] = url.password
        if url.database:
            argv += [url.database]
        return argv, env

    raise SystemExit(
        f"`manage.py dbshell` doesn't know how to open a shell for driver "
        f"'{driver}'. Supported: sqlite, postgresql, mysql/mariadb."
    )


def execute(args: argparse.Namespace) -> None:
    from fastframe.core.settings import load_settings

    settings = load_settings(None)
    database_url = getattr(settings, "DATABASE_URL", None)
    if not database_url:
        raise SystemExit("DATABASE_URL is not set.")

    argv, extra_env = build_dbshell_command(database_url)
    env = os.environ.copy()
    env.update(extra_env)
    try:
        os.execvpe(argv[0], argv, env)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"'{argv[0]}' not found on PATH. Install the client for your database."
        ) from exc
