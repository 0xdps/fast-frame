from __future__ import annotations

import os
from typing import Any

from alembic import command
from alembic.config import Config

from fastframe.core.bootstrap import bootstrap, get_apps_registry
from fastframe.core.settings import load_settings
from fastframe.db.engine import get_engine
from fastframe.migrations.ownership import group_operations, table_owners
from fastframe.migrations.paths import (
    app_migration_dirs,
    get_script_location,
    get_version_locations,
)


def build_alembic_config(settings_module: str | None = None) -> Config:
    bootstrap(settings_module)
    settings = load_settings(settings_module)
    registry = get_apps_registry()
    script_location = get_script_location(settings_module)
    cfg = Config()
    cfg.set_main_option("script_location", str(script_location))
    cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
    version_locations = get_version_locations(registry, settings_module)
    cfg.set_main_option("path_separator", "os")
    cfg.set_main_option(
        "version_locations",
        os.pathsep.join(str(path) for path in version_locations),
    )
    return cfg


def makemigrations(
    message: str = "auto",
    settings_module: str | None = None,
    app_labels: list[str] | None = None,
) -> None:
    """Generate migrations, one file per app that actually changed.

    Each project app's operations are written to ``<app>/migrations``.
    Framework apps (dotted names such as ``fastframe.contrib.auth``) share
    ``config/migrations``, because they are not a directory in the project.
    Files are chained in that order so a later app can reference an earlier
    app's tables, but a change to one app is never written into another
    app's migration directory.
    """
    from alembic.operations import ops
    from alembic.util import rev_id

    cfg = build_alembic_config(settings_module)
    registry = get_apps_registry()
    dirs = app_migration_dirs(registry, settings_module)
    owners = table_owners(registry)
    requested = _requested_apps(app_labels, dirs)

    written: list[str] = []

    def process_revision_directives(context, revision, directives):
        del context, revision
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] = []
            return

        groups, skipped = group_operations(
            list(script.upgrade_ops.ops),
            list(script.downgrade_ops.ops),
            owners,
            list(dirs),
            only=requested,
        )
        if skipped:
            names = ", ".join(skipped)
            print(f"Left unchanged apps for a later makemigrations: {names}")
        if not groups:
            directives[:] = []
            return

        head: str | None = script.head or "head"
        upgrade_token = script.upgrade_ops.upgrade_token
        downgrade_token = script.downgrade_ops.downgrade_token
        replacement: list[ops.MigrationScript] = []
        for app_name, upgrade, downgrade in groups:
            new_id = rev_id()
            replacement.append(
                ops.MigrationScript(
                    rev_id=new_id,
                    message=message,
                    upgrade_ops=ops.UpgradeOps(upgrade, upgrade_token=upgrade_token),
                    downgrade_ops=ops.DowngradeOps(downgrade, downgrade_token=downgrade_token),
                    head=head,
                    splice=False,
                    branch_label=None,
                    version_path=str(dirs[app_name]),
                    imports=set(),
                )
            )
            written.append(app_name)
            head = new_id
        directives[:] = replacement

    command.revision(
        cfg,
        message=message,
        autogenerate=True,
        process_revision_directives=process_revision_directives,
    )

    if not written:
        print("No changes detected.")


def migrate(revision: str = "head", settings_module: str | None = None) -> None:
    cfg = build_alembic_config(settings_module)
    command.upgrade(cfg, revision)


def _requested_apps(app_labels: list[str] | None, dirs: dict[str, object]) -> set[str] | None:
    if not app_labels:
        return None
    from fastframe.migrations.paths import FRAMEWORK_MIGRATION_APP

    resolved: set[str] = set()
    unknown: list[str] = []
    for label in app_labels:
        if label in dirs:
            resolved.add(label)
        elif "." in label and FRAMEWORK_MIGRATION_APP in dirs:
            # ``fastframe.contrib.auth`` and other packaged apps share config/.
            resolved.add(FRAMEWORK_MIGRATION_APP)
        else:
            unknown.append(label)
    if unknown:
        known = ", ".join(dirs) or "(none)"
        missing = ", ".join(unknown)
        raise SystemExit(f"Unknown app(s): {missing}. Known migration owners: {known}")
    return resolved


def _migration_owner(path: str) -> str:
    from pathlib import Path

    parts = Path(path).parts
    if "migrations" in parts:
        index = parts.index("migrations")
        if index > 0:
            return parts[index - 1]
    return "migrations"


def showmigrations(settings_module: str | None = None) -> None:
    """Print migrations grouped by the app that owns the file.

    Each revision is marked ``[X]`` (applied) or ``[ ]`` (pending).
    """
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    cfg = build_alembic_config(settings_module)
    script = ScriptDirectory.from_config(cfg)

    revisions = list(script.walk_revisions())
    if not revisions:
        print("No migrations found. Run `manage.py makemigrations`.")
        return

    try:
        engine = get_engine(settings_module)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_heads = set(context.get_current_heads())
    except Exception as exc:  # noqa: BLE001 - degrade to "unknown applied state"
        print(f"Could not determine applied migrations: {exc}\n")
        current_heads = set()

    applied: set[str] = set()
    for head in current_heads:
        for rev in script.walk_revisions(base="base", head=head):
            applied.add(rev.revision)

    # walk_revisions() with no base/head walks newest -> oldest across all
    # heads; reverse for chronological order, then group by owning app.
    grouped: dict[str, list[Any]] = {}
    order: list[str] = []
    for rev in reversed(revisions):
        owner = _migration_owner(str(rev.path))
        if owner not in grouped:
            order.append(owner)
            grouped[owner] = []
        grouped[owner].append(rev)

    for owner in order:
        print(owner)
        for rev in grouped[owner]:
            marker = "X" if rev.revision in applied else " "
            doc = rev.doc or ""
            print(f" [{marker}] {rev.revision} {doc}".rstrip())
