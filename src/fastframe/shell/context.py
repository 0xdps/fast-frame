from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

from fastframe.core.apps import AppsRegistry
from fastframe.models.base import Model


class ShellStartupError(RuntimeError):
    pass


def _import_models(registry: AppsRegistry, namespace: dict[str, object]) -> None:
    for app_config in registry.app_configs:
        try:
            models_module = importlib.import_module(f"{app_config.name}.models")
        except ModuleNotFoundError:
            continue
        for attr_name in dir(models_module):
            attr = getattr(models_module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Model)
                and attr is not Model
                and getattr(attr, "__tablename__", None)
            ):
                namespace[attr_name] = attr


def _run_import_lines(lines: list[str], namespace: dict[str, object]) -> None:
    for line in lines:
        statement = line.strip()
        if not statement or statement.startswith("#"):
            continue
        exec(compile(statement, "<SHELL_IMPORTS>", "exec"), namespace, namespace)


def _resolve_startup_path(settings: ModuleType) -> Path | None:
    startup = getattr(settings, "SHELL_STARTUP", None)
    if startup is None:
        base_dir = getattr(settings, "BASE_DIR", None)
        if base_dir is None:
            return None
        default = Path(base_dir) / "config" / "shell_startup.py"
        return default if default.is_file() else None
    path = Path(startup)
    if not path.is_absolute():
        base_dir = getattr(settings, "BASE_DIR", Path.cwd())
        path = Path(base_dir) / path
    return path if path.is_file() else None


def _run_startup_file(path: Path, namespace: dict[str, object]) -> None:
    source = path.read_text(encoding="utf-8")
    exec(compile(source, str(path), "exec"), namespace, namespace)


def _run_app_shell_hooks(registry: AppsRegistry, namespace: dict[str, object]) -> None:
    for app_config in registry.app_configs:
        hook = getattr(app_config, "shell", None)
        if callable(hook):
            hook(namespace)


def build_shell_namespace(
    registry: AppsRegistry,
    session: object,
) -> dict[str, object]:
    """Build the local namespace for ``manage.py shell`` (stdlib REPL)."""
    settings = registry.settings
    namespace: dict[str, object] = {
        "settings": settings,
        "session": session,
    }

    if getattr(settings, "SHELL_AUTO_IMPORT_MODELS", True):
        _import_models(registry, namespace)

    imports = getattr(settings, "SHELL_IMPORTS", None)
    if imports:
        if not isinstance(imports, (list, tuple)):
            raise ShellStartupError("SHELL_IMPORTS must be a list of import statements.")
        _run_import_lines([str(line) for line in imports], namespace)

    startup_path = _resolve_startup_path(settings)
    if startup_path is not None:
        _run_startup_file(startup_path, namespace)

    _run_app_shell_hooks(registry, namespace)
    return namespace
