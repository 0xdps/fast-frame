"""FastFrame configuration system.

Defaults live in ``global_settings``. A project's ``FASTFRAME_SETTINGS_MODULE``
overrides them. Values are loaded lazily so importing FastFrame before the
environment variable is set still picks up the project settings on first use.
``bootstrap()`` reloads them explicitly.
"""

from __future__ import annotations

import importlib
import os
from typing import Any


class Settings:
    """Defaults from global_settings, overridden by the project settings module."""

    def __init__(self) -> None:
        self._loaded = False

    def reload(self) -> None:
        """Re-read global defaults and the current settings module."""
        for key in [name for name in self.__dict__ if name.isupper()]:
            del self.__dict__[key]

        global_settings = importlib.import_module("fastframe.conf.global_settings")
        for name in dir(global_settings):
            if name.isupper():
                setattr(self, name, getattr(global_settings, name))

        module_name = os.environ.get("FASTFRAME_SETTINGS_MODULE")
        if module_name:
            user_settings = importlib.import_module(module_name)
            for name in dir(user_settings):
                if name.isupper():
                    setattr(self, name, getattr(user_settings, name))
        self._loaded = True

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        self.reload()
        try:
            return self.__dict__[name]
        except KeyError as exc:
            raise AttributeError(f"Setting {name!r} is not defined") from exc


settings = Settings()