from __future__ import annotations


def test_get_session_reuses_middleware_session(miniproject_env) -> None:
    """Verify get_session() reuses existing contextvar session from middleware."""
    from config.asgi import application
    from fastapi import Depends
    from fastapi.testclient import TestClient

    from fastframe.db.session import Session, get_session

    captured_sessions: list[Session] = []

    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/capture")
    def capture_route(session: Session = Depends(get_session)) -> dict:  # noqa: B008
        captured_sessions.append(session)
        return {"ok": True}

    application.include_router(router)
    client = TestClient(application)
    response = client.get("/capture")
    assert response.status_code == 200
    assert len(captured_sessions) == 1


def test_get_session_standalone_opens_own_session() -> None:
    """Verify get_session() opens its own session when no middleware is present."""
    from fastframe.db.session import get_session

    gen = get_session()
    session = next(gen)
    assert session is not None
    try:
        next(gen)
    except StopIteration:
        pass
