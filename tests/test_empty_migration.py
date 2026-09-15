from __future__ import annotations


def test_makemigrations_skips_empty_revision(miniproject_env, capsys) -> None:
    """Verify makemigrations skips creating a migration when no changes are detected."""
    from fastframe.migrations.runner import makemigrations
    
    # After the fixture, DB is already migrated, so no changes should be detected
    makemigrations(settings_module=None)
    
    captured = capsys.readouterr()
    assert "No changes detected" in captured.out
