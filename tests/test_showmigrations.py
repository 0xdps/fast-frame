from __future__ import annotations


def test_showmigrations_lists_applied_revision(miniproject_env, capsys) -> None:
    from fastframe.migrations.runner import showmigrations

    showmigrations()
    out = capsys.readouterr().out
    assert "[X]" in out


def test_showmigrations_no_migrations(miniproject_env, monkeypatch, capsys) -> None:
    """If there are no migration files at all, print a helpful message
    instead of empty/confusing output.
    """
    from alembic.script import ScriptDirectory

    class _EmptyScriptDirectory:
        def walk_revisions(self, *args: object, **kwargs: object) -> list[object]:
            return []

    monkeypatch.setattr(
        ScriptDirectory, "from_config", classmethod(lambda cls, *a, **kw: _EmptyScriptDirectory())
    )

    from fastframe.migrations.runner import showmigrations

    showmigrations()
    out = capsys.readouterr().out
    assert "No migrations found" in out
