# MVP v0.1

The first version stays deliberately small. Objective: **prove the FastFrame development loop** before expanding toward a broader Django-like feature set.

## Feature status

| Feature | v0.1 target |
| --- | --- |
| FastAPI integration | Yes |
| Project creation | Yes |
| App / module creation | Yes |
| Configuration / settings | Yes |
| Routing (router discovery) | Yes |
| Models (thin manager API) | Yes |
| Migrations | Yes |
| Interactive shell | Yes |
| Development server | Yes |
| Environment / config management | Yes (minimal) |
| Basic error handling | Yes (FastAPI defaults + debug-friendly behavior) |
| Testing integration | Yes |
| Admin | Later |
| Authentication | Later |
| Templates | Later |
| Static files | Later |
| Background jobs | Later |
| Caching | Later |
| Email | Later |
| Storage | Later |

## Signature loop

```text
FastFrame
│
├── FastAPI (routers, as-is)
├── Models (thin helpers + SQLAlchemy)
├── Migrations (Alembic, wrapped)
└── Shell

manage.py  →  central developer interface inside a project
fastframe  →  global CLI (e.g. startproject) before manage.py exists
```

## manage.py commands (target)

```text
python manage.py runserver
python manage.py shell
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py check
python manage.py startapp <name>    # may also exist on fastframe; TBD
```

`check` may be minimal in v0.1 (settings load, apps import). `check --deploy` is post–v0.1.

## Model API (initial, intentionally small)

Planned convenience methods (exact names subject to design):

- `objects.all()`
- `objects.filter(**kwargs)`
- `objects.exclude(**kwargs)` (optional v0.1)
- `objects.get(...)`
- `objects.first()`
- `objects.count()`
- `objects.create(...)`
- instance `save()`, `delete()`

Anything beyond this → **SQLAlchemy** with the project's session.

## Migrations workflow

```text
python manage.py makemigrations
python manage.py migrate
```

Developers should not manually configure Alembic for a standard project.

## Shell

```text
python manage.py shell
```

Application initialized: settings, database, model discovery. Example experience:

```python
>>> User.objects.count()
42
>>> User.objects.filter(is_active=True)
[...]
>>> User.objects.get(id=1)
```

Future: `--ipython`, `--ptpython`; stdlib REPL remains the fallback.

## Development server

```text
python manage.py runserver
```

Uvicorn runs underneath; normal development does not require manual Uvicorn configuration.

## Configuration (v0.1)

Keep minimal:

- Environment variables
- Database URL / SQLite default
- `INSTALLED_APPS`
- Debug flag
- Logging basics

Defer static/media settings until those features exist.

## Default technical choices (v0.1)

| Choice | Note |
| --- | --- |
| Database default | SQLite for zero-decision start |
| HTTP | Sync SQLAlchemy session in requests unless async strategy is chosen explicitly — see [session-lifecycle.md](session-lifecycle.md) |
| Tests | pytest via `manage.py test` |

## Success criteria

v0.1 succeeds if a developer can complete the full loop without reading deep internals docs, and:

- Hard queries feel like a **natural** SQLAlchemy drop-down, not a framework dead-end.
- HTTP code is **pasteable FastAPI**, not a parallel view API.
- A third-party package can eventually register as an **installed app** (contract defined in [app-contract.md](app-contract.md)).

## Explicit v0.1 cuts

- Django-style views and URL regex dispatch
- Full QuerySet algebra (`Q`, `F`, deep chaining)
- Admin, auth, templates, static
- Optional component registry with many backends
- Production deployment platform
