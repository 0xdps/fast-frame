"""Regression test: admin auto-discovers every installed app's ``admin.py``.

A project should be able to drop ``admin_site.register(...)`` at the module
level of ``<app>/admin.py`` and have it take effect simply by listing the
app in ``INSTALLED_APPS`` — no manual import of the admin module required.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

from fastframe.core.bootstrap import reset_bootstrap


@pytest.fixture
def app_with_admin_py(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Create a throwaway app package with an ``admin.py`` that registers
    a model, put it on ``sys.path``, and boot a settings module that lists
    it (plus the admin battery) in ``INSTALLED_APPS``.
    """
    app_dir = tmp_path / "myadminapp"
    app_dir.mkdir()
    (app_dir / "__init__.py").write_text("", encoding="utf-8")
    (app_dir / "models.py").write_text(
        'from fastframe.models import Model, fields\n'
        'class Widget(Model):\n'
        '    __tablename__ = "widgets"\n'
        '    name = fields.CharField(max_length=100)\n',
        encoding="utf-8",
    )
    (app_dir / "admin.py").write_text(
        'from fastframe.admin import ModelAdmin, admin_site\n'
        'from .models import Widget\n'
        'class WidgetAdmin(ModelAdmin):\n'
        '    list_display = ["name"]\n'
        'admin_site.register(Widget, WidgetAdmin)\n',
        encoding="utf-8",
    )
    # A minimal AppConfig isn't required — a bare app (no apps.py) is skipped
    # gracefully by populate_apps and still reaches the admin.py import.

    settings_dir = tmp_path / "settings_mod"
    settings_dir.mkdir()
    (settings_dir / "__init__.py").write_text("", encoding="utf-8")
    (settings_dir / "settings.py").write_text(
        'INSTALLED_APPS = [\n'
        '    "fastframe.contrib.auth",\n'
        '    "fastframe.admin",\n'
        '    "myadminapp",\n'
        ']\n'
        'DATABASE_URL = "sqlite:///:memory:"\n'
        'AUTH_USER_MODEL = "auth.User"\n',
        encoding="utf-8",
    )

    sys.path.insert(0, str(tmp_path))
    monkeypatch.setenv("FASTFRAME_SETTINGS_MODULE", "settings_mod.settings")
    reset_bootstrap()
    yield
    reset_bootstrap()
    sys.path.remove(str(tmp_path))
    # Undo the registration this module-level import performed.
    from fastframe.admin import admin_site

    widget = importlib.import_module("myadminapp.models").Widget
    if admin_site.is_registered(widget):
        admin_site.unregister(widget)


def test_installed_app_admin_py_is_auto_discovered(app_with_admin_py) -> None:
    """Listing an app in INSTALLED_APPS imports its admin.py automatically."""
    from fastframe.admin import admin_site
    from fastframe.core.bootstrap import bootstrap

    bootstrap(None)

    from myadminapp.models import Widget

    assert admin_site.is_registered(Widget)
    assert admin_site.get_model_admin(Widget).list_display == ["name"]