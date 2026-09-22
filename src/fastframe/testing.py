"""Test utilities for projects built on FastFrame.

Not imported by the framework itself at runtime — only useful in tests.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from types import ModuleType

_MISSING = object()


@contextmanager
def override_settings(**overrides: object) -> Iterator[ModuleType]:
    """Temporarily set attributes on the currently loaded settings module.

    Requires FastFrame to already be bootstrapped (e.g. via the project
    template's `project_env`/`client` fixtures). Restores the previous
    values — or removes the attribute entirely if it didn't exist before —
    when the context manager exits, even if the test raises.

    Example:

        from fastframe.testing import override_settings

        def test_feature_flag_disabled(client):
            with override_settings(FEATURE_X_ENABLED=False):
                response = client.get("/feature-x")
                assert response.status_code == 404
    """
    from fastframe.core.bootstrap import get_apps_registry

    settings = get_apps_registry().settings
    originals: dict[str, object] = {}
    for key, value in overrides.items():
        originals[key] = getattr(settings, key, _MISSING)
        setattr(settings, key, value)
    try:
        yield settings
    finally:
        for key, original in originals.items():
            if original is _MISSING:
                delattr(settings, key)
            else:
                setattr(settings, key, original)
