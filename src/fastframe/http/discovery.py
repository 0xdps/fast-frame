"""Discover ``FastFrameAPI`` objects declared by installed apps.

An app opts in by defining ``api`` in ``<app>.api``. The path is explicit
on each route. The module name is not a URL.
"""

from __future__ import annotations

import importlib
from typing import Any

from fastapi import APIRouter

from fastframe.core.apps import AppsRegistry
from fastframe.http.api import FastFrameAPI


def discover_api_routers(registry: AppsRegistry) -> list[APIRouter]:
    """Return routers from each installed app's ``api`` module, in order.

    A missing ``api`` module is normal. An ``api`` module with no ``api``
    attribute is also skipped, so a native-only module is not an error.
    """
    routers: list[APIRouter] = []
    for config in registry.app_configs:
        if not config.name:
            continue
        try:
            module = importlib.import_module(f"{config.name}.api")
        except ModuleNotFoundError:
            continue
        api = getattr(module, "api", None)
        router = _router_from(api)
        if router is not None:
            routers.append(router)
    return routers


def _router_from(api: Any) -> APIRouter | None:
    if isinstance(api, FastFrameAPI):
        return api.router
    if isinstance(api, APIRouter):
        return api
    return None
