# Public API (v0.1 + v0.2)

Surfaces intended to remain **stable** across minor releases. Everything else is experimental until documented here. v0.2 additions are called out inline.

## Global CLI (`fastframe`)

| Command | Description |
| --- | --- |
| `fastframe startproject <name>` | Create project directory and files |
| (optional) `fastframe startapp <name>` | Create app inside project — may live only on `manage.py` |

Entry point (future): `fastframe = fastframe.cli.main:main`

## Project CLI (`manage.py`)

| Command | Description |
| --- | --- |
| `runserver` | Dev server (Uvicorn); Django-style `addrport` positional arg |
| `shell` | Bootstrapped REPL (models auto-imported; `SHELL_IMPORTS`/`shell_startup.py`/`AppConfig.shell()` hooks) |
| `makemigrations` | Autogenerate schema migrations (Alembic) |
| `migrate` | Apply migrations (`head` by default) |
| `showmigrations` | List migrations with `[X]`/`[ ]` applied markers |
| `dbshell` | Open the native DB client (sqlite3/psql/mysql) |
| `test` | Run pytest with app context; forwards flags straight through, no `--` needed |
| `check` / `check --database` | Structural + optional DB/migration checks (`fastframe.core.checks`) |
| `startapp <name>` | Scaffold app package |
| `--version` | Print the installed FastFrame version |

## Settings

- Module: an ordinary importable Python module, `config.settings` by default — resolved via `FASTFRAME_SETTINGS_MODULE`, not a special settings object/metaclass.
- Required concepts: `INSTALLED_APPS`, `DATABASE_URL` (or equivalent), `DEBUG`.
- `.env` files are loaded (via `python-dotenv`, without overriding real env vars) before the settings module is imported — see [app-contract.md](app-contract.md#settings).

Exact names will match implementation; breaking renames require CHANGELOG + ADR.

## Application factory

- `get_asgi_application()` — returns ASGI callable for production servers.

## Database

- `get_session` — FastAPI dependency for request-scoped session (`fastframe.db`).
- `session_scope()` — context manager for shell/tests.
- `get_current_session()` — active session for managers and raw SQLAlchemy.

## Models

- `Model` — declarative base (`fastframe.models`).
- `Model.objects` — `all`, `filter`, `exclude`, `order_by`, `get`, `first`, `exists`, `count`, `create`; instance `save`, `delete`.
- `QuerySet` — lazy, chainable (`filter().order_by().limit().offset()`), list-like (`for`, `len`, `[i]`); returned by `all`/`filter`/`exclude`/`order_by`.
- `DoesNotExist`, `MultipleObjectsReturned` — manager lookup errors; auto-converted to HTTP 404/500 by `get_asgi_application()`'s exception handlers.

## Checks and lifecycle (v0.2)

- `AppConfig.ready()` — bootstrap-time hook (v0.1).
- `AppConfig.checks()` — return `list[CheckMessage]`; backs `manage.py check` (`fastframe.core.checks`).
- `AppConfig.shutdown()` — ASGI lifespan shutdown hook.

## Testing utilities (v0.2)

- `fastframe.testing.override_settings(**kwargs)` — context manager to temporarily override settings-module attributes within a test.

## Routing helpers (v0.2)

- `fastframe.http.pagination.pagination` — FastAPI dependency (`Depends(pagination)`) parsing `?limit=&offset=` into a `Pagination(limit, offset)`. `Pagination.apply(queryset)` calls `.limit().offset()` on a `QuerySet`. Not re-exported from `fastframe.http` — import from `fastframe.http.pagination` directly (see the module's docstring for why).

## Re-exports (optional convenience)

May re-export unchanged symbols:

```python
from fastapi import APIRouter, Depends, HTTPException
```

Re-exports are not wrappers; they do not change behavior.

## Explicitly not stable

- Internal Alembic layout — currently a single combined revision chain (see [app-contract.md](app-contract.md)), may change
- Migration file naming beyond "works for standard apps"
- Custom management command auto-discovery (`<app>/management/commands/`) — deferred to v0.6+, not implemented

## Versioning

Package version follows SemVer. Pre-1.0, minor bumps may adjust draft APIs documented as experimental.
