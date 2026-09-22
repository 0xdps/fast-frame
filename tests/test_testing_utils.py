from __future__ import annotations


def test_override_settings_restores_previous_value(miniproject_env) -> None:
    from fastframe.core.bootstrap import get_apps_registry
    from fastframe.testing import override_settings

    settings = get_apps_registry().settings
    settings.APP_NAME = "original"

    with override_settings(APP_NAME="overridden"):
        assert get_apps_registry().settings.APP_NAME == "overridden"

    assert get_apps_registry().settings.APP_NAME == "original"


def test_override_settings_removes_attribute_that_did_not_exist(miniproject_env) -> None:
    from fastframe.core.bootstrap import get_apps_registry
    from fastframe.testing import override_settings

    settings = get_apps_registry().settings
    assert not hasattr(settings, "BRAND_NEW_FLAG")

    with override_settings(BRAND_NEW_FLAG=True):
        assert get_apps_registry().settings.BRAND_NEW_FLAG is True

    assert not hasattr(settings, "BRAND_NEW_FLAG")


def test_override_settings_restores_on_exception(miniproject_env) -> None:
    from fastframe.core.bootstrap import get_apps_registry
    from fastframe.testing import override_settings

    settings = get_apps_registry().settings
    settings.APP_NAME = "original"

    try:
        with override_settings(APP_NAME="overridden"):
            raise ValueError("boom")
    except ValueError:
        pass

    assert get_apps_registry().settings.APP_NAME == "original"
