"""Application core: settings, apps registry, bootstrap."""

from fastframe.core.apps import AppConfig
from fastframe.core.bootstrap import bootstrap, get_apps_registry

__all__ = ["AppConfig", "bootstrap", "get_apps_registry"]
