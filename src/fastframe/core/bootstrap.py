from __future__ import annotations

from fastframe.core.apps import AppsRegistry, populate_apps
from fastframe.core.settings import load_settings

_registry: AppsRegistry | None = None


def bootstrap(settings_module: str | None = None) -> AppsRegistry:
    """Load settings, build the app registry, and run AppConfig.ready()."""
    global _registry
    settings = load_settings(settings_module)
    from fastframe.conf import settings as conf_settings

    conf_settings.reload()
    registry = populate_apps(settings)
    # Make the registry available *before* running ready() hooks, so an
    # app's ready() can discover sibling apps (e.g. fastframe.admin imports
    # every installed app's admin.py to register models).
    _registry = registry
    for app_config in registry.app_configs:
        app_config.ready()

    # Resolve any pending forward-referenced FK/M2M targets (e.g. a field
    # declared as `fields.ForeignKey("Later")` where "Later" is defined
    # further down the same module, or in a model imported after this one)
    # now that every installed app's models have been imported — before
    # any caller does `Model.metadata.create_all()`, which needs M2M join
    # tables to already exist in `Model.metadata` to create them.
    from sqlalchemy.orm import configure_mappers

    configure_mappers()

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
