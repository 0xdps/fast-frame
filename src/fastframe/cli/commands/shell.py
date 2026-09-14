from __future__ import annotations

import argparse
import code


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Use the plain Python REPL (default)",
    )


def execute(args: argparse.Namespace) -> None:
    import importlib

    from fastframe.core.bootstrap import bootstrap
    from fastframe.db.init import import_app_models
    from fastframe.db.session import begin_session, end_session
    from fastframe.models.base import Model

    registry = bootstrap(None)
    import_app_models(registry)
    settings = registry.settings

    session, token = begin_session(None)
    banner = (
        "FastFrame interactive shell\n"
        "Models are loaded; `User.objects`-style managers use the active session.\n"
        "Type exit() or Ctrl-D to quit."
    )
    local_namespace: dict[str, object] = {
        "settings": settings,
        "session": session,
    }
    for app_config in registry.app_configs:
        try:
            models_module = importlib.import_module(f"{app_config.name}.models")
        except ModuleNotFoundError:
            continue
        for attr_name in dir(models_module):
            attr = getattr(models_module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, Model)
                and attr is not Model
                and getattr(attr, "__tablename__", None)
            ):
                local_namespace[attr_name] = attr
    try:
        code.interact(banner=banner, local=local_namespace)
        end_session(session, token, commit=True)
    except SystemExit:
        end_session(session, token, commit=True)
        raise
    except KeyboardInterrupt:
        end_session(session, token, commit=False)
    except Exception:
        end_session(session, token, commit=False)
        raise
