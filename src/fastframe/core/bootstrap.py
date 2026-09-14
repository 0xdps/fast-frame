from __future__ import annotations

from fastframe.core.apps import AppsRegistry, populate_apps
from fastframe.core.settings import load_settings

_registry: AppsRegistry | None = None


def bootstrap(settings_module: str | None = None) -> AppsRegistry:
    """Load settings, build the app registry, and run AppConfig.ready()."""
    global _registry
    settings = load_settings(settings_module)
    registry = populate_apps(settings)
    for app_config in registry.app_configs:
        app_config.ready()
    _registry = registry
    return registry


def get_apps_registry() -> AppsRegistry:
    if _registry is None:
        raise RuntimeError("FastFrame is not bootstrapped. Call bootstrap() first.")
    return _registry


def reset_bootstrap() -> None:
    """Clear bootstrap state (for tests)."""
    global _registry
    _registry = None
    from fastframe.db.engine import reset_engine
    from fastframe.db.session import reset_session_factory

    reset_session_factory()
    reset_engine()
