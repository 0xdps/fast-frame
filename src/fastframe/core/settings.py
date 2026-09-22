from __future__ import annotations

import importlib
import os
from types import ModuleType

_dotenv_loaded = False


class SettingsError(RuntimeError):
    pass


def _load_dotenv_once() -> None:
    """Load a `.env` file (if any) into `os.environ`, once per process.

    Searches upward from the current working directory (`manage.py`
    commands are always run from the project root by convention). Never
    overrides variables already set in the real environment — a `.env`
    file is a convenience default, not a source of truth that should win
    over an operator's actual environment (e.g. in a container/CI).
    Silently does nothing if `python-dotenv` isn't installed or no `.env`
    file is found.

    NOTE: `usecwd=True` is required here. `python-dotenv`'s default
    `find_dotenv()` walks up from the *caller's file location* (inspected
    via the call stack) rather than the process's current working
    directory — which for us means it would search upward from wherever
    `fastframe` itself is installed (e.g. site-packages), never finding a
    project's `.env` at all. `usecwd=True` makes it search from `os.getcwd()`
    instead, matching where `manage.py` is actually run from.
    """
    global _dotenv_loaded
    if _dotenv_loaded:
        return
    _dotenv_loaded = True
    try:
        from dotenv import find_dotenv, load_dotenv
    except ImportError:
        return
    dotenv_path = find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)


def get_settings_module_name(explicit: str | None = None) -> str:
    _load_dotenv_once()
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
