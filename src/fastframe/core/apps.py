from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from types import ModuleType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import APIRouter

    from fastframe.core.checks import CheckMessage


class AppConfig:
    """Base configuration for an installed application."""

    name: str = ""
    label: str = ""

    def ready(self) -> None:
        """Hook run after the app registry is loaded."""

    def shutdown(self) -> None:
        """Hook run when the ASGI app shuts down (see `get_asgi_application()`).

        Not called for CLI commands (`manage.py shell`, `check`, etc.) —
        those are short-lived processes; use `try`/`finally` there instead.
        """

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

    def get_routers(self) -> list[APIRouter]:
        """Return FastAPI routers this app wants mounted, if any.

        Called by ``get_asgi_application()``/``create_app()`` for every
        installed app, in ``INSTALLED_APPS`` order, *after* every app's
        ``ready()`` has already run. This is how being listed in
        ``INSTALLED_APPS`` — and nothing else — turns a router on: the
        router-building code (and anything it imports) only runs for apps
        that are actually installed, the same way ``models.py`` is only
        imported for installed apps (see ``fastframe.db.init.import_app_models``).

        The base implementation returns nothing — plain apps that only
        want the existing ``urls.py`` → ``router`` convention (aggregated
        via a project's ``ROOT_URLCONF``) don't need to override this.
        Override it when an app (typically a framework-provided one, e.g.
        ``fastframe.admin``) needs to build its router(s) programmatically
        from settings rather than exposing a static module-level `router`.
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

    def is_installed(self, app_name: str) -> bool:
        """Whether ``app_name`` is present in ``INSTALLED_APPS`` (by name).

        This is the mechanism for making a feature "not forced": code
        that lazily imports/mounts something should check this instead of
        a dedicated ``ENABLE_*`` boolean, so the feature genuinely isn't
        imported unless the project opted in by listing it as an app —
        the same way any other app's models/routers are opt-in.
        """
        return any(config.name == app_name for config in self.app_configs)

    def get_routers(self) -> list[Any]:
        """Collect every installed app's ``get_routers()``, in order."""
        routers: list[Any] = []
        for config in self.app_configs:
            routers.extend(config.get_routers())
        return routers


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
