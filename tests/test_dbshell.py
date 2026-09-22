from __future__ import annotations

import pytest

from fastframe.cli.commands.dbshell import build_dbshell_command


def test_dbshell_sqlite() -> None:
    argv, env = build_dbshell_command("sqlite:///./db.sqlite3")
    assert argv == ["sqlite3", "./db.sqlite3"]
    assert env == {}


def test_dbshell_sqlite_memory() -> None:
    argv, env = build_dbshell_command("sqlite:///:memory:")
    assert argv[0] == "sqlite3"


def test_dbshell_postgresql() -> None:
    argv, env = build_dbshell_command("postgresql://alice:secret@dbhost:5433/mydb")
    assert argv[0] == "psql"
    assert "-h" in argv and "dbhost" in argv
    assert "-p" in argv and "5433" in argv
    assert "-U" in argv and "alice" in argv
    assert argv[-1] == "mydb"
    assert env == {"PGPASSWORD": "secret"}


def test_dbshell_postgresql_no_password() -> None:
    argv, env = build_dbshell_command("postgresql://alice@dbhost/mydb")
    assert "PGPASSWORD" not in env


def test_dbshell_mysql() -> None:
    argv, env = build_dbshell_command("mysql://bob:pw@localhost:3306/appdb")
    assert argv[0] == "mysql"
    assert "-u" in argv and "bob" in argv
    assert env == {"MYSQL_PWD": "pw"}


def test_dbshell_unsupported_driver() -> None:
    with pytest.raises(SystemExit, match="doesn't know how to open a shell"):
        build_dbshell_command("oracle://user:pw@host/db")
