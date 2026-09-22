"""System check framework.

Mirrors the shape of Django's ``manage.py check``: apps and the framework
itself register lightweight, structured messages instead of raising
exceptions or printing ad-hoc text. ``manage.py check`` collects and prints
them, and exits non-zero if any ERROR/CRITICAL messages were found.

Apps opt in by overriding :meth:`fastframe.core.apps.AppConfig.checks`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastframe.core.apps import AppsRegistry

# Severity levels, ordered like Python's logging module / Django's checks.
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

_LEVEL_NAMES = {
    DEBUG: "DEBUG",
    INFO: "INFO",
    WARNING: "WARNING",
    ERROR: "ERROR",
    CRITICAL: "CRITICAL",
}


@dataclass
class CheckMessage:
    """A single result from a system check.

    Attributes:
        level: One of the module-level constants (DEBUG..CRITICAL).
        message: Human-readable description of the issue.
        hint: Optional actionable suggestion (e.g. "Run manage.py migrate").
        id: Optional stable identifier (e.g. "fastframe.W001") for silencing
            or documentation cross-referencing later.
        obj: Optional label for what the message is about (e.g. an app
            label). Defaults to "?" when printed if unset.
    """

    level: int
    message: str
    hint: str | None = None
    id: str | None = None
    obj: str | None = None

    @property
    def level_name(self) -> str:
        return _LEVEL_NAMES.get(self.level, str(self.level))

    def __str__(self) -> str:
        label = self.obj or "?"
        prefix = f"{self.id}: " if self.id else ""
        text = f"{label}: {prefix}{self.message}"
        if self.hint:
            text += f"\n\tHINT: {self.hint}"
        return text


def is_serious(messages: list[CheckMessage]) -> bool:
    """True if any message is ERROR level or above (should fail CI/exit 1)."""
    return any(m.level >= ERROR for m in messages)


def run_checks(
    registry: AppsRegistry,
    *,
    include_database: bool = False,
    settings_module: str | None = None,
) -> list[CheckMessage]:
    """Run built-in framework checks plus every app's ``checks()`` hook.

    Structural checks (settings shape, duplicate app labels) always run and
    require no I/O. Database checks (connectivity, pending migrations) only
    run when ``include_database=True``, matching Django's opt-in
    ``check --database`` behavior — so a plain ``manage.py check`` stays
    fast and safe to run before a database even exists.
    """
    messages: list[CheckMessage] = []

    messages.extend(_check_installed_apps(registry))
    messages.extend(_check_duplicate_labels(registry))
    messages.extend(_check_database_url(registry))

    if include_database:
        messages.extend(_check_database_connection(registry, settings_module))
        messages.extend(_check_pending_migrations(registry, settings_module))

    for app_config in registry.app_configs:
        hook = getattr(app_config, "checks", None)
        if not callable(hook):
            continue
        try:
            app_messages = hook() or []
        except Exception as exc:  # noqa: BLE001 - isolate a broken app's checks
            messages.append(
                CheckMessage(
                    level=CRITICAL,
                    message=f"checks() raised an exception: {exc!r}",
                    id="fastframe.C001",
                    obj=app_config.label,
                )
            )
            continue
        for msg in app_messages:
            if msg.obj is None:
                msg.obj = app_config.label
            messages.append(msg)

    return messages


# --- Built-in checks -------------------------------------------------------


def _check_installed_apps(registry: AppsRegistry) -> list[CheckMessage]:
    if not registry.app_configs:
        return [
            CheckMessage(
                level=WARNING,
                message="INSTALLED_APPS is empty.",
                hint="Add at least one app to INSTALLED_APPS in settings.",
                id="fastframe.W001",
                obj="settings",
            )
        ]
    return []


def _check_duplicate_labels(registry: AppsRegistry) -> list[CheckMessage]:
    seen: dict[str, int] = {}
    for app_config in registry.app_configs:
        seen[app_config.label] = seen.get(app_config.label, 0) + 1
    duplicates = [label for label, count in seen.items() if count > 1]
    if not duplicates:
        return []
    return [
        CheckMessage(
            level=ERROR,
            message=(
                f"Duplicate app label '{label}' used by {seen[label]} apps. "
                "Set a unique `label` on each AppConfig."
            ),
            id="fastframe.E001",
            obj="settings",
        )
        for label in duplicates
    ]


def _check_database_url(registry: AppsRegistry) -> list[CheckMessage]:
    database_url = getattr(registry.settings, "DATABASE_URL", None)
    if not database_url:
        return [
            CheckMessage(
                level=ERROR,
                message="DATABASE_URL is not set.",
                hint="Set DATABASE_URL in settings (e.g. sqlite:///./db.sqlite3).",
                id="fastframe.E002",
                obj="settings",
            )
        ]
    return []


def _check_database_connection(
    registry: AppsRegistry,
    settings_module: str | None,
) -> list[CheckMessage]:
    from fastframe.db.engine import get_engine

    try:
        engine = get_engine(settings_module)
        with engine.connect():
            pass
    except Exception as exc:  # noqa: BLE001 - report, don't crash `check`
        return [
            CheckMessage(
                level=ERROR,
                message=f"Could not connect to the database: {exc}",
                hint="Check DATABASE_URL and that the database server is reachable.",
                id="fastframe.E003",
                obj="database",
            )
        ]
    return []


def _check_pending_migrations(
    registry: AppsRegistry,
    settings_module: str | None,
) -> list[CheckMessage]:
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory

    from fastframe.db.engine import get_engine
    from fastframe.migrations.runner import build_alembic_config

    try:
        cfg = build_alembic_config(settings_module)
        script = ScriptDirectory.from_config(cfg)
        heads = set(script.get_heads())

        engine = get_engine(settings_module)
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_heads = set(context.get_current_heads())
    except Exception as exc:  # noqa: BLE001 - report, don't crash `check`
        return [
            CheckMessage(
                level=ERROR,
                message=f"Could not determine migration status: {exc}",
                id="fastframe.E004",
                obj="migrations",
            )
        ]

    pending = heads - current_heads
    if not pending:
        return []
    return [
        CheckMessage(
            level=WARNING,
            message=f"You have {len(pending)} unapplied migration(s).",
            hint="Run `manage.py migrate`.",
            id="fastframe.W002",
            obj="migrations",
        )
    ]
