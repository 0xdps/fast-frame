"""Find management commands shipped by installed apps.

An app registers a command by placing a module at
``<app>/management/commands/<name>.py``. The module name is the command
name. It defines ``execute(args)`` and, optionally, ``add_arguments(parser)``.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType


class CommandError(Exception):
    """An installed app's management command cannot be loaded."""


def discover_app_commands() -> dict[str, ModuleType]:
    """Return app command modules keyed by command name.

    Raises ``SettingsError`` when no settings module is configured, and
    ``CommandError`` when an installed app's command is missing
    ``execute``, uses a built-in name, or repeats a name from another app.
    An app with no ``management/commands`` package contributes nothing.
    """
    from fastframe.cli.manage import COMMANDS
    from fastframe.core.settings import load_settings

    settings = load_settings(None)
    installed = getattr(settings, "INSTALLED_APPS", None) or []
    found: dict[str, ModuleType] = {}
    owners: dict[str, str] = {}
    for app_name in installed:
        if not isinstance(app_name, str) or not app_name.strip():
            raise CommandError("INSTALLED_APPS entries must be app import paths.")
        package = _commands_package(app_name)
        if package is None:
            continue
        for module_name in _command_module_names(package):
            module = importlib.import_module(f"{package.__name__}.{module_name}")
            _require_execute(module)
            if module_name in COMMANDS:
                raise CommandError(f'"{app_name}" defines "{module_name}", which is already a built-in command.')
            if module_name in found:
                raise CommandError(f'"{module_name}" is defined by both "{owners[module_name]}" and "{app_name}".')
            found[module_name] = module
            owners[module_name] = app_name
    return dict(sorted(found.items()))


def _commands_package(app_name: str) -> ModuleType | None:
    commands_name = f"{app_name}.management.commands"
    management_name = f"{app_name}.management"
    try:
        package = importlib.import_module(commands_name)
    except ModuleNotFoundError as exc:
        if exc.name in {commands_name, management_name}:
            return None
        if exc.name == app_name or (exc.name and app_name.startswith(f"{exc.name}.")):
            raise CommandError(f'Cannot import installed app "{app_name}".') from exc
        raise
    if getattr(package, "__path__", None) is None:
        return None
    return package


def _command_module_names(package: ModuleType) -> list[str]:
    names: list[str] = []
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.ispkg or module_info.name.startswith("_"):
            continue
        names.append(module_info.name)
    return names


def _require_execute(module: ModuleType) -> None:
    execute = getattr(module, "execute", None)
    if not callable(execute):
        raise CommandError(f"{module.__name__} must define execute(args) to be a management command.")
    add_arguments = getattr(module, "add_arguments", None)
    if add_arguments is not None and not callable(add_arguments):
        raise CommandError(f"{module.__name__} add_arguments must be a function.")
