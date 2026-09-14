# Architecture

FastFrame is modular internally: a small **core** plus **components** that participate in a shared application lifecycle.

## Conceptual diagram

```text
                    FastFrame
                        │
              ┌─────────┴─────────┐
              │                   │
             Core             Components
              │                   │
       ┌──────┴──────┐       ┌────┴─────┐
       │             │       │          │
    FastAPI       Config   Models    Migrations
    (HTTP)                    │          │
                          SQLAlchemy   Alembic
```

## Layers (planned)

| Layer | Role | Technology |
| --- | --- | --- |
| HTTP / ASGI | Routing, validation, OpenAPI | FastAPI, Pydantic |
| Server (dev) | Development server | Uvicorn (hidden behind `runserver`) |
| Configuration | Settings, env, installed apps | FastFrame conventions + Pydantic Settings |
| CLI | Global + project commands | `fastframe` + `manage.py` |
| Models | Declaration, discovery, thin manager API | SQLAlchemy (mapped classes) |
| Migrations | Developer workflow | Alembic (convention-driven, not user-configured for standard projects) |
| Shell | Bootstrapped REPL | stdlib Python; configurable imports |
| Testing | Discover and run tests | pytest integration |

## HTTP layer

**FastAPI is the view layer.** FastFrame discovers and mounts routers from installed apps; it does not introduce Django-style views.

## Data layer

Models are SQLAlchemy models with a **thin manager** (`filter`, `get`, `save`, …). Complex operations use SQLAlchemy explicitly.

## Future optional components

These are **not** v0.1 core. They should attach via the same app/lifecycle model:

- Admin
- Authentication / authorization
- Templates (e.g. Jinja2)
- Static / media files
- Background tasks
- Caching
- Email
- Storage
- Signals / events (only if justified)
- Observability helpers

## Modularity model (target)

```text
Core
├── API integration (FastAPI app factory)
├── Configuration
├── Routing discovery
├── CLI
└── Lifecycle (startup, app loading)

Optional (apps or contrib packages)
├── Models / ORM helpers
├── Migrations
├── Shell
├── Admin
├── Auth
├── Templates
├── Static
├── Tasks
├── Cache
├── Email
└── Storage
```

Exact configuration mechanism for enabling optional components will be decided during MVP implementation; v0.1 may ship a single sensible default bundle (models + migrations + shell) without a full plugin registry.

## Generated project layout (target)

```text
myproject/
├── manage.py
├── pyproject.toml
├── config/
│   ├── settings.py
│   ├── urls.py          # aggregates app routers
│   ├── asgi.py
│   └── __init__.py
├── users/                 # example app from startapp
│   ├── models.py
│   ├── urls.py            # APIRouter export
│   ├── migrations/
│   └── __init__.py
└── tests/
```

Exact names may evolve; the goal is **predictable, convention-driven** layout.
