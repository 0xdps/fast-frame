from __future__ import annotations


def test_build_shell_namespace_models_and_imports(miniproject_env) -> None:
    from users.models import User

    from fastframe.core.bootstrap import bootstrap
    from fastframe.db.session import begin_session, end_session
    from fastframe.shell.context import build_shell_namespace

    registry = bootstrap(None)
    session, token = begin_session(None)
    try:
        namespace = build_shell_namespace(registry, session)
    finally:
        end_session(session, token, commit=False)

    assert namespace["User"] is User
    assert "session_scope" in namespace
    assert "health_router" in namespace


def test_app_shell_hook(miniproject_env) -> None:
    from fastframe.core.apps import AppConfig
    from fastframe.core.bootstrap import bootstrap
    from fastframe.db.session import begin_session, end_session
    from fastframe.shell.context import build_shell_namespace

    class HookConfig(AppConfig):
        name = "health"
        label = "health"

        def shell(self, context: dict) -> None:
            context["hook_ran"] = True

    registry = bootstrap(None)
    registry.app_configs = [HookConfig()]
    session, token = begin_session(None)
    try:
        namespace = build_shell_namespace(registry, session)
    finally:
        end_session(session, token, commit=False)

    assert namespace["hook_ran"] is True
