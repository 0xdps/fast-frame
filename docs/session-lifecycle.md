# Session lifecycle (draft)

One of the highest-risk areas for FastFrame is **database session scope**. Django hides connections; FastAPI + SQLAlchemy require an explicit story. This document captures the intended rules before implementation.

## Goals

1. **One documented rule** for how a session is obtained in:
   - HTTP requests
   - `manage.py shell`
   - tests (`manage.py test` / pytest)
2. **Same session object** exposed to the thin model manager and to SQLAlchemy escape hatches.
3. **Predictable transaction boundaries** (commit/rollback) per request and per test.

## Public API (planned)

- `get_session` — FastAPI dependency (e.g. `Depends(get_session)`).
- Possibly `Session` alias for typing convenience.
- Shell and tests use the same factory, not ad hoc engine creation.

Implemented in v0.1 scaffold:

- `fastframe.db.get_session` — FastAPI dependency (optional; middleware also binds a session per request).
- `fastframe.db.session_scope` — shell/tests context manager.
- `fastframe.db.get_current_session` — escape hatch for SQLAlchemy and managers.
- HTTP middleware in `get_asgi_application()` opens/commits/rolls back a sync session per request.

## HTTP request (sync-first default)

**Draft default for v0.1:** synchronous SQLAlchemy session per request.

1. Dependency opens session at request start.
2. Route handlers and `Model.objects.*` use that session.
3. On success: commit (or flush policy TBD).
4. On exception: rollback.
5. Session closed after response.

Async endpoints and `asyncpg` / async SQLAlchemy are **out of scope for v0.1** unless explicitly chosen before coding starts. If deferred, document “sync ORM + async routes” limitations clearly.

## Shell

`manage.py shell`:

1. Load settings and initialize FastFrame.
2. Create a session bound to the configured engine.
3. Bind session to model managers (or a thread-local / contextvar registry).
4. User imports models and runs queries.

Open question: auto-commit in shell vs explicit `session.commit()` — leaning toward explicit commit in shell for safety.

## Tests

pytest fixtures (provided by FastFrame):

- Engine/database setup (SQLite in memory or test DB URL).
- Session per test function (or per test module — TBD).
- Rollback or truncate between tests for isolation.

Tests must not require copy-pasting session wiring from application code.

## Thin manager + SQLAlchemy

Example escape hatch (illustrative):

```python
from sqlalchemy import select
from fastframe.db import get_session  # or current session accessor — TBD

stmt = select(User).where(User.email.endswith("@example.com"))
session = ...  # same session as User.objects
session.execute(stmt).scalars().all()
```

The exact “current session” accessor for non-request code must be defined in implementation (contextvar recommended).

## Decisions needed before coding

| Decision | Options |
| --- | --- |
| Sync vs async v0.1 | Sync-only default strongly recommended |
| Commit policy in requests | Commit on success vs manual |
| Session registry | contextvar vs explicit pass-through |
| Multi-database | Defer past v0.1 |

Record outcomes in ADRs when locked.
