from __future__ import annotations

import importlib

from fastframe.core.apps import AppsRegistry
from fastframe.db.engine import get_engine
from fastframe.models.base import Model


def import_app_models(registry: AppsRegistry) -> None:
    for app_config in registry.app_configs:
        try:
            importlib.import_module(f"{app_config.name}.models")
        except ModuleNotFoundError:
            continue


def create_tables(settings_module: str | None, registry: AppsRegistry) -> None:
    import_app_models(registry)
    engine = get_engine(settings_module)
    Model.metadata.create_all(bind=engine)
