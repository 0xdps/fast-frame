from __future__ import annotations

from collections.abc import Generator, Iterator
from contextlib import contextmanager
from contextvars import ContextVar

from sqlalchemy.orm import Session, sessionmaker

from fastframe.db.engine import get_engine

_session_ctx: ContextVar[Session | None] = ContextVar("fastframe_db_session", default=None)
_session_factory: sessionmaker[Session] | None = None


class SessionNotConfiguredError(RuntimeError):
    pass


def _get_session_factory(settings_module: str | None = None) -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(settings_module), autoflush=True)
    return _session_factory


def get_current_session() -> Session:
    session = _session_ctx.get()
    if session is None:
        raise SessionNotConfiguredError(
            "No active database session. Use get_session in routes or session_scope()."
        )
    return session


@contextmanager
def session_scope(settings_module: str | None = None) -> Iterator[Session]:
    """Open a session and bind it to the current context (shell, tests)."""
    session = _get_session_factory(settings_module)()
    token = _session_ctx.set(session)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        _session_ctx.reset(token)


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency: one session per request.
    
    If middleware has already bound a session, reuses it.
    Otherwise opens a new session (e.g. for standalone routers).
    """
    existing = _session_ctx.get()
    if existing is not None:
        # Reuse middleware session; don't commit/close here
        yield existing
        return
    
    # Standalone use: manage our own session
    session = _get_session_factory()()
    token = _session_ctx.set(session)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        _session_ctx.reset(token)


def reset_session_factory() -> None:
    global _session_factory
    _session_factory = None


def begin_session(settings_module: str | None = None) -> tuple[Session, object]:
    """Attach a new session to the current context (used by HTTP middleware)."""
    session = _get_session_factory(settings_module)()
    token = _session_ctx.set(session)
    return session, token


def end_session(session: Session, token: object, *, commit: bool) -> None:
    try:
        if commit:
            session.commit()
        else:
            session.rollback()
    finally:
        session.close()
        _session_ctx.reset(token)
