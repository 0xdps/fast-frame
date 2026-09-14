from __future__ import annotations

import importlib
import os
from types import ModuleType


class SettingsError(RuntimeError):
    pass


def get_settings_module_name(explicit: str | None = None) -> str:
    name = explicit or os.environ.get("FASTFRAME_SETTINGS_MODULE")
    if not name:
        raise SettingsError(
            "Settings module not configured. Set FASTFRAME_SETTINGS_MODULE "
            "(e.g. config.settings) or pass settings_module to bootstrap()."
        )
    return name


def load_settings(settings_module: str | None = None) -> ModuleType:
    module_name = get_settings_module_name(settings_module)
    return importlib.import_module(module_name)
