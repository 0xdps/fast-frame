from __future__ import annotations

import importlib
from pathlib import Path

from fastframe.core.apps import AppsRegistry
from fastframe.core.settings import load_settings
from fastframe.models.base import Model


def get_base_dir(settings_module: str | None = None) -> Path:
    settings = load_settings(settings_module)
    base_dir = getattr(settings, "BASE_DIR", None)
    if base_dir is None:
        return Path.cwd()
    return Path(base_dir)


def get_script_location(settings_module: str | None = None) -> Path:
    settings = load_settings(settings_module)
    base_dir = get_base_dir(settings_module)
    relative = getattr(settings, "ALEMBIC_SCRIPT_LOCATION", "config/migrations")
    return base_dir / relative


def _app_has_models(app_name: str) -> bool:
    try:
        module = importlib.import_module(f"{app_name}.models")
    except ModuleNotFoundError:
        return False
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, Model)
            and attr is not Model
            and getattr(attr, "__tablename__", None)
        ):
            return True
    return False


# Framework apps (``fastframe.contrib.auth``, ``fastframe.admin``, …) are
# installed packages, not a directory under the project. Their migration
# files live in the project's ``config/migrations`` rather than being
# appended to whichever local app happens to be listed first.
FRAMEWORK_MIGRATION_APP = "config"


def _versions_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def app_migration_dirs(
    registry: AppsRegistry,
    settings_module: str | None = None,
) -> dict[str, Path]:
    """Map each migration owner to its ``versions`` directory.

    Order is generation order: framework models first (so a later app can
    reference them), then each project app in ``INSTALLED_APPS`` order.
    Project apps own ``<app>/migrations/versions``. Framework apps share
    ``config/migrations/versions``.
    """
    base_dir = get_base_dir(settings_module)
    dirs: dict[str, Path] = {}
    has_framework_models = False
    for app_config in registry.app_configs:
        if not _app_has_models(app_config.name):
            continue
        if "." in app_config.name:
            has_framework_models = True
            continue
        dirs[app_config.name] = _versions_dir(
            base_dir / app_config.name / "migrations" / "versions"
        )
    if has_framework_models or not dirs:
        # Insert config first so framework tables are created before app
        # tables that reference them, without displacing project apps.
        config_dir = _versions_dir(base_dir / "config" / "migrations" / "versions")
        dirs = {FRAMEWORK_MIGRATION_APP: config_dir, **dirs}
    return dirs


def get_version_locations(
    registry: AppsRegistry,
    settings_module: str | None = None,
) -> list[Path]:
    return list(app_migration_dirs(registry, settings_module).values())


def default_version_path(
    registry: AppsRegistry,
    settings_module: str | None = None,
) -> Path:
    return get_version_locations(registry, settings_module)[0]
