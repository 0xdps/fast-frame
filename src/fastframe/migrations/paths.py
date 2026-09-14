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


def get_version_locations(
    registry: AppsRegistry,
    settings_module: str | None = None,
) -> list[Path]:
    base_dir = get_base_dir(settings_module)
    locations: list[Path] = []
    for app_config in registry.app_configs:
        if not _app_has_models(app_config.name):
            continue
        path = base_dir / app_config.name / "migrations" / "versions"
        path.mkdir(parents=True, exist_ok=True)
        locations.append(path)
    if not locations:
        fallback = base_dir / "config" / "migrations" / "versions"
        fallback.mkdir(parents=True, exist_ok=True)
        locations.append(fallback)
    return locations


def default_version_path(
    registry: AppsRegistry,
    settings_module: str | None = None,
) -> Path:
    return get_version_locations(registry, settings_module)[0]
