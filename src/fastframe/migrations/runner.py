from __future__ import annotations

import os

from alembic import command
from alembic.config import Config

from fastframe.core.bootstrap import bootstrap, get_apps_registry
from fastframe.core.settings import load_settings
from fastframe.migrations.paths import (
    default_version_path,
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


def makemigrations(message: str = "auto", settings_module: str | None = None) -> None:
    cfg = build_alembic_config(settings_module)
    registry = get_apps_registry()
    version_path = str(default_version_path(registry, settings_module))
    command.revision(
        cfg,
        message=message,
        autogenerate=True,
        version_path=version_path,
    )


def migrate(revision: str = "head", settings_module: str | None = None) -> None:
    cfg = build_alembic_config(settings_module)
    command.upgrade(cfg, revision)
