from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.pool import StaticPool

from fastframe.core.settings import load_settings

_engine: Engine | None = None


def get_engine(settings_module: str | None = None) -> Engine:
    global _engine
    if _engine is None:
        settings = load_settings(settings_module)
        url = getattr(settings, "DATABASE_URL", "sqlite:///./db.sqlite3")
        connect_args: dict[str, object] = {}
        engine_kwargs: dict[str, object] = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        if url.endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool
        _engine = create_engine(url, connect_args=connect_args, **engine_kwargs)
    return _engine


def reset_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.dispose()
    _engine = None
