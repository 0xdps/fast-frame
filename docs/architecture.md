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

## Layers

| Layer | Role | Technology |
| --- | --- | --- |
| HTTP / ASGI | Routing, validation, OpenAPI | FastAPI, Pydantic |
| Server (dev) | Development server | Uvicorn (hidden behind `runserver`) |
| Configuration | Settings, env, installed apps | FastFrame conventions (settings module reload, `.env` support) |
| CLI | Global + project commands | `fastframe` + `manage.py` |
| Models | Declaration, discovery, thin manager API | SQLAlchemy (mapped classes + declarative `fields.*`) |
| Migrations | Developer workflow | Alembic (convention-driven, not user-configured for standard projects) |
| Shell | Bootstrapped REPL | stdlib Python; configurable imports |
| Testing | Discover and run tests | pytest integration |
| Admin | CRUD UI + REST API, session auth | `fastframe.admin` — on by default (`ENABLE_ADMIN`), see [admin-setup.md](admin-setup.md) |
| Auth & permissions | User model, session/token auth, `Group`/permission strings | `fastframe.contrib.auth` — on by default (`ENABLE_AUTH_API`), see [auth.md](auth.md), [permissions.md](permissions.md) |
| REST API | Generic token-authenticated CRUD, non-admin routes | `fastframe.api` — **opt-in** (`ENABLE_REST_API`), see [rest-api.md](rest-api.md) |

## HTTP layer

**FastAPI is the view layer.** FastFrame discovers and mounts routers from installed apps; it does not introduce Django-style views.

## Data layer

Models are SQLAlchemy models with a **thin manager** (`filter`, `get`, `save`, …). Complex operations use SQLAlchemy explicitly.

## Shipped components (not core, but on by default)

Admin and auth attach via the same app/lifecycle model as everything
else, but ship in `fastframe` itself (not a separate package) and
default to **on** — `ENABLE_ADMIN` and `ENABLE_AUTH_API` are both `True`
unless a project opts out. The compiled admin UI assets are
force-included in every built wheel regardless of whether a project
enables admin (`pyproject.toml`'s `[tool.hatch.build.targets.wheel.force-include]`).
This is a deliberate, known departure from "batteries included, not
forced" for these two — worth revisiting if it starts happening for
every future component below too.

- Admin (`fastframe.admin`)
- Authentication / authorization (`fastframe.contrib.auth`)
- Generic REST API (`fastframe.api`) — genuinely opt-in (`ENABLE_REST_API`, default `False`)
- Audit log (`fastframe.admin.audit`) — follows admin/REST API's on-by-default posture

## Future optional components

Not yet built. Unlike the above, these should be **opt-in from the
start** — not imported, not mounted, unless a project explicitly enables
them — to avoid `create_app()` slowly becoming the monolith the
[design principles](design-principles.md) warn against:

- Templates (e.g. Jinja2) and static/media files — next up, see [roadmap.md](roadmap.md)
- Background tasks
- Caching
- Email
- Storage
- Signals / events (only if justified)
- Observability helpers

## Modularity model

```text
Core
├── API integration (FastAPI app factory: create_app())
├── Configuration (settings module, ENABLE_* flags)
├── Routing discovery (installed-app routers)
├── CLI (fastframe + manage.py)
└── Lifecycle (bootstrap(), AppConfig.ready()/checks()/shutdown())

Shipped, on by default (ENABLE_ADMIN / ENABLE_AUTH_API default True)
├── Models / ORM helpers
├── Migrations
├── Shell
├── Admin
└── Auth & permissions

Shipped, opt-in (default False)
└── Generic REST API (ENABLE_REST_API)

Future, opt-in from the start (not yet built)
├── Templates
├── Static
├── Tasks
├── Cache
├── Email
└── Storage
```

Enabling/disabling a component is a settings flag
(`ENABLE_ADMIN`/`ENABLE_AUTH_API`/`ENABLE_REST_API`), checked in
`create_app()` before that component's router is even imported — not a
full plugin registry. Every future component should follow the "opt-in,
not imported unless enabled" pattern of `ENABLE_REST_API`, not the
on-by-default pattern of admin/auth.

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
