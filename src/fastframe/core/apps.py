from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from types import ModuleType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastframe.core.checks import CheckMessage


class AppConfig:
    """Base configuration for an installed application."""

    name: str = ""
    label: str = ""

    def ready(self) -> None:
        """Hook run after the app registry is loaded."""

    def checks(self) -> list[CheckMessage]:
        """Hook run by ``manage.py check``. Return a list of CheckMessage.

        Override to validate app-specific configuration, e.g.:

            from fastframe.core.checks import CheckMessage, WARNING

            class BillingConfig(AppConfig):
                def checks(self) -> list[CheckMessage]:
                    if not getattr(settings, "STRIPE_KEY", None):
                        return [CheckMessage(level=WARNING, message="STRIPE_KEY not set.")]
                    return []
        """
        return []

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.name:
            cls.name = cls.__module__.rsplit(".", 1)[0]
        if not cls.label:
            cls.label = cls.name.rsplit(".", 1)[-1]


@dataclass
class AppsRegistry:
    settings: ModuleType
    app_configs: list[AppConfig] = field(default_factory=list)


def _app_config_from_module(app_name: str) -> AppConfig:
    try:
        apps_module = importlib.import_module(f"{app_name}.apps")
    except ModuleNotFoundError:
        config = AppConfig()
        config.name = app_name
        config.label = app_name.rsplit(".", 1)[-1]
        return config

    for attr_name in dir(apps_module):
        attr = getattr(apps_module, attr_name)
        if (
            isinstance(attr, type)
            and issubclass(attr, AppConfig)
            and attr is not AppConfig
        ):
            instance = attr()
            if not instance.name:
                instance.name = app_name
            return instance

    config = AppConfig()
    config.name = app_name
    config.label = app_name.rsplit(".", 1)[-1]
    return config


def populate_apps(settings: ModuleType) -> AppsRegistry:
    installed = getattr(settings, "INSTALLED_APPS", None)
    if installed is None:
        raise ValueError("Settings must define INSTALLED_APPS")

    registry = AppsRegistry(settings=settings)
    for app_name in installed:
        config = _app_config_from_module(app_name)
        registry.app_configs.append(config)
    return registry
