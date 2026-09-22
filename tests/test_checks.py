from __future__ import annotations

import argparse
from types import ModuleType

import pytest

from fastframe.core.apps import AppConfig, AppsRegistry
from fastframe.core.checks import (
    CRITICAL,
    ERROR,
    WARNING,
    CheckMessage,
    is_serious,
    run_checks,
)


def _settings(**overrides: object) -> ModuleType:
    module = ModuleType("fake_settings")
    module.INSTALLED_APPS = overrides.pop("INSTALLED_APPS", ["fake_app"])
    module.DATABASE_URL = overrides.pop("DATABASE_URL", "sqlite:///:memory:")
    for key, value in overrides.items():
        setattr(module, key, value)
    return module


def test_check_message_str_includes_hint() -> None:
    msg = CheckMessage(level=WARNING, message="Something's off.", hint="Fix it.", obj="myapp")
    text = str(msg)
    assert "myapp" in text
    assert "Something's off." in text
    assert "HINT: Fix it." in text


def test_is_serious_true_for_error_and_above() -> None:
    assert is_serious([CheckMessage(level=ERROR, message="x")])
    assert is_serious([CheckMessage(level=CRITICAL, message="x")])
    assert not is_serious([CheckMessage(level=WARNING, message="x")])
    assert not is_serious([])


def test_run_checks_warns_on_empty_installed_apps() -> None:
    registry = AppsRegistry(settings=_settings(), app_configs=[])
    messages = run_checks(registry)
    ids = [m.id for m in messages]
    assert "fastframe.W001" in ids


def test_run_checks_errors_on_missing_database_url() -> None:
    settings = _settings(DATABASE_URL="")
    registry = AppsRegistry(settings=settings, app_configs=[AppConfig()])
    messages = run_checks(registry)
    ids = [m.id for m in messages]
    assert "fastframe.E002" in ids
    assert is_serious(messages)


def test_run_checks_detects_duplicate_labels() -> None:
    a = AppConfig()
    a.name = "app_one"
    a.label = "shared"
    b = AppConfig()
    b.name = "app_two"
    b.label = "shared"
    registry = AppsRegistry(settings=_settings(), app_configs=[a, b])

    messages = run_checks(registry)
    ids = [m.id for m in messages]
    assert "fastframe.E001" in ids
    assert is_serious(messages)


def test_run_checks_calls_app_checks_hook() -> None:
    class NoisyConfig(AppConfig):
        name = "noisy"
        label = "noisy"

        def checks(self) -> list[CheckMessage]:
            return [CheckMessage(level=WARNING, message="custom warning")]

    registry = AppsRegistry(settings=_settings(), app_configs=[NoisyConfig()])
    messages = run_checks(registry)

    custom = [m for m in messages if m.message == "custom warning"]
    assert len(custom) == 1
    assert custom[0].obj == "noisy"


def test_run_checks_isolates_broken_app_checks_hook() -> None:
    class BrokenConfig(AppConfig):
        name = "broken"
        label = "broken"

        def checks(self) -> list[CheckMessage]:
            raise RuntimeError("boom")

    registry = AppsRegistry(settings=_settings(), app_configs=[BrokenConfig()])
    # Should not raise; the broken app's failure becomes a CRITICAL message.
    messages = run_checks(registry)
    critical = [m for m in messages if m.level == CRITICAL]
    assert len(critical) == 1
    assert "boom" in critical[0].message


def test_run_checks_catches_unimportable_app() -> None:
    typo_app = AppConfig()
    typo_app.name = "definitely_not_a_real_module_xyz"
    typo_app.label = "definitely_not_a_real_module_xyz"
    registry = AppsRegistry(settings=_settings(), app_configs=[typo_app])

    messages = run_checks(registry)
    ids = [m.id for m in messages]
    assert "fastframe.E005" in ids
    assert is_serious(messages)


def test_run_checks_allows_real_importable_app() -> None:
    real_app = AppConfig()
    real_app.name = "fastframe"
    real_app.label = "fastframe"
    registry = AppsRegistry(settings=_settings(), app_configs=[real_app])

    messages = run_checks(registry)
    ids = [m.id for m in messages]
    assert "fastframe.E005" not in ids


def test_default_app_config_checks_returns_empty_list() -> None:
    assert AppConfig().checks() == []


def test_check_command_exits_nonzero_on_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
    import importlib

    from fastframe.cli.commands import check as check_cmd

    fake_registry = AppsRegistry(settings=_settings(DATABASE_URL=""), app_configs=[])
    # `fastframe.core.__init__` re-exports `bootstrap` under the same name
    # as the `fastframe.core.bootstrap` submodule, which shadows the
    # submodule on the *parent package's* attribute table. Both plain
    # attribute traversal (`import a.b.c as x`) and pytest's string-target
    # `monkeypatch.setattr("a.b.c", ...)` resolve via that attribute table
    # and would patch the re-exported function instead of the submodule.
    # `importlib.import_module` resolves via `sys.modules` instead, so it
    # reliably returns the actual submodule.
    bootstrap_submodule = importlib.import_module("fastframe.core.bootstrap")
    monkeypatch.setattr(bootstrap_submodule, "bootstrap", lambda _sm: fake_registry)

    with pytest.raises(SystemExit) as exc_info:
        check_cmd.execute(argparse.Namespace())
    assert exc_info.value.code == 1

    out = capsys.readouterr().out
    assert "fastframe.E002" in out
    assert "System check identified" in out


def test_check_command_bare_namespace_defaults_database_to_false(
    miniproject_env, capsys: pytest.CaptureFixture
) -> None:
    """A Namespace without `database` set (e.g. constructed directly, not via
    argparse) should not blow up — `--database` should default to False."""
    from fastframe.cli.commands.check import execute

    execute(argparse.Namespace())  # no `database` attribute at all
    out = capsys.readouterr().out
    assert "no issues" in out
