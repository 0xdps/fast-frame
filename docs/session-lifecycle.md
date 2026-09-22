# Session lifecycle

One of the highest-risk areas for FastFrame is **database session scope**. Django hides connections; FastAPI + SQLAlchemy require an explicit story. This document records the decisions FastFrame ships with, as of v0.1/v0.2 — no more open questions.

## Goals

1. **One documented rule** for how a session is obtained in:
   - HTTP requests
   - `manage.py shell`
   - tests (`manage.py test` / pytest)
2. **Same session object** exposed to the thin model manager and to SQLAlchemy escape hatches.
3. **Predictable transaction boundaries** (commit/rollback) per request and per test.

## Public API (`fastframe.db`)

- `get_session` — FastAPI dependency (`Depends(get_session)`). Reuses the middleware-bound session if one exists (the normal HTTP case); opens and manages its own otherwise (standalone routers, ad hoc scripts).
- `get_current_session()` — the "current session" accessor for non-request code (managers, SQLAlchemy escape hatches, shell). Backed by a `ContextVar`; raises `SessionNotConfiguredError` if nothing has bound a session yet.
- `session_scope()` — context manager for shell/tests/scripts. Commits on clean exit, rolls back on exception.
- `begin_session()` / `end_session()` — lower-level pair used by the HTTP middleware and `manage.py shell` to bind/unbind a session around a longer-lived block with custom commit logic.

Implemented in `fastframe/db/session.py`.

## HTTP requests (sync)

Synchronous SQLAlchemy session per request — the only supported mode in v0.1/v0.2. Async endpoints and async SQLAlchemy are **out of scope**; document "sync ORM + async routes" as a known limitation rather than half-supporting it.

1. `db_session_middleware` (installed by `get_asgi_application()`) opens a session at request start via `begin_session()`.
2. Route handlers and `Model.objects.*` use that session via `get_current_session()` / `Depends(get_session)`.
3. **On success: commit.** On any exception: rollback. Always closed after the response, regardless of outcome.

## `manage.py shell`

1. Bootstrap, then `begin_session()` binds a session for the whole REPL.
2. Models are auto-imported into the namespace; `session` is also exposed directly.
3. **Commit policy: commit on clean exit** (REPL closed normally, or `exit()`/Ctrl-D → `SystemExit`). **Roll back on Ctrl-C or any other exception** escaping the REPL loop. This favors "don't lose an intentional session's work" while still protecting against a half-finished interactive block from silently persisting.

## Tests

pytest fixtures provided by the project template (`tests/conftest.py`):

- **Session/DB scope: per test function.** `project_env` (and the framework's own `miniproject_env`) is a function-scoped fixture that sets `DATABASE_URL` to a fresh in-memory SQLite DB, calls `reset_bootstrap()`, and re-migrates — so every test function gets an isolated database, not just an isolated session.
- The `client` fixture builds the FastAPI `TestClient` *inside* the fixture, after `project_env` has configured `DATABASE_URL` — never import `config.asgi.application` at module level in a test file, or it gets built against whatever `DATABASE_URL` was active at collection time. See the fixture's docstring for the full footgun.
- `fastframe.testing.override_settings(**kwargs)` — a context manager for temporarily overriding attributes on the already-loaded settings module within a single test, for cases where per-test env vars aren't enough (e.g. toggling a feature flag). Restores the original values on exit.

```python
from fastframe.testing import override_settings

def test_feature_flag_disabled(client):
    from config import settings

    with override_settings(FEATURE_X_ENABLED=False):
        response = client.get("/feature-x")
        assert response.status_code == 404
```

## Thin manager + SQLAlchemy escape hatch

```python
from sqlalchemy import select
from fastframe.db import get_current_session

stmt = select(User).where(User.email.endswith("@example.com"))
session = get_current_session()  # same session as User.objects
session.execute(stmt).scalars().all()
```

## Decisions (locked)

| Decision | Outcome |
| --- | --- |
| Sync vs async v0.1/v0.2 | Sync-only |
| Commit policy in requests | Commit on success, rollback on exception |
| Commit policy in shell | Commit on clean exit, rollback on Ctrl-C/exception |
| Session registry | `ContextVar` (`get_current_session()`) |
| Test isolation | Per test function; fresh DB, not just fresh session |
| Multi-database | Still deferred — no story planned before v1.0 |

Record any future changes to these as ADRs.
