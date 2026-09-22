# Public API v0.1 (draft)

Surfaces intended to remain **stable** across minor releases once v0.1 ships. Everything else is experimental until documented here.

## Global CLI (`fastframe`)

| Command | Description |
| --- | --- |
| `fastframe startproject <name>` | Create project directory and files |
| (optional) `fastframe startapp <name>` | Create app inside project — may live only on `manage.py` |

Entry point (future): `fastframe = fastframe.cli.main:main`

## Project CLI (`manage.py`)

| Command | Description |
| --- | --- |
| `runserver` | Dev server (Uvicorn) |
| `shell` | Bootstrapped REPL |
| `makemigrations` | Generate migrations from models |
| `migrate` | Apply migrations |
| `test` | Run pytest with app context |
| `check` / `check --database` | Structural + optional DB/migration checks (`fastframe.core.checks`) |
| `startapp <name>` | Scaffold app package |
| `makemigrations` | Autogenerate schema migrations (Alembic) |
| `migrate` | Apply migrations (`head` by default) |

## Settings

- Conventional module: `config/settings.py` (or `settings` object — TBD).
- Required concepts: `INSTALLED_APPS`, `DATABASE_URL` (or equivalent), `DEBUG`.

Exact names will match implementation; breaking renames require CHANGELOG + ADR.

## Application factory

- `get_asgi_application()` — returns ASGI callable for production servers.

## Database

- `get_session` — FastAPI dependency for request-scoped session (`fastframe.db`).
- `session_scope()` — context manager for shell/tests.
- `get_current_session()` — active session for managers and raw SQLAlchemy.

## Models

- `Model` — declarative base (`fastframe.models`).
- `Model.objects` — `all`, `filter`, `get`, `first`, `count`, `create`; instance `save`, `delete`.
- `DoesNotExist`, `MultipleObjectsReturned` — manager lookup errors.

## Re-exports (optional convenience)

May re-export unchanged symbols:

```python
from fastapi import APIRouter, Depends, HTTPException
```

Re-exports are not wrappers; they do not change behavior.

## Explicitly not stable in v0.1

- Internal Alembic layout
- Migration file naming beyond “works for standard apps”
- Undocumented hooks in `AppConfig.ready()`

## Versioning

Package version follows SemVer. Pre-1.0, minor bumps may adjust draft APIs documented as experimental.
