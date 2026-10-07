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
| Admin | CRUD UI + REST API, session auth | `fastframe.admin` — opt-in, add to `INSTALLED_APPS`, see [admin-setup.md](admin-setup.md) |
| Auth & permissions | User model, session/token auth, `Group`/permission strings | `fastframe.contrib.auth` — opt-in, add to `INSTALLED_APPS`, see [auth.md](auth.md), [permissions.md](permissions.md) |
| REST API | Generic token-authenticated CRUD, non-admin routes | `fastframe.api` — opt-in, add to `INSTALLED_APPS`, see [rest-api.md](rest-api.md) |

## HTTP layer

**FastAPI is the view layer.** FastFrame discovers and mounts routers from installed apps; it does not introduce Django-style views.

## Data layer

Models are SQLAlchemy models with a **thin manager** (`filter`, `get`, `save`, …). Complex operations use SQLAlchemy explicitly.

## Shipped components ("batteries" — not core, opt-in like any other app)

Admin, auth, the generic REST API, OpenAPI docs, and the health check attach via the *exact same*
app-registry mechanism as a project's own apps: they ship inside
`fastframe` itself (not a separate package), but nothing about them
runs — no import, no router, no side effect — unless a project lists
them in `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    "fastframe.health",  # GET /health — a new project includes this one
    "fastframe.contrib.auth",  # User/Group models + /api/auth/*
    "fastframe.admin",  # /admin UI + /api/admin/*
    "fastframe.api",  # token-authenticated /api/v1/*
    "fastframe.docs",  # /docs, /redoc, /openapi.json
    "myapp",
]
```

Each exposes an `AppConfig` (`ready()` for import-time side effects,
`get_routers()` for the routers it wants mounted — see
[app-contract.md](app-contract.md)), resolved the same way as any other
`INSTALLED_APPS` entry. A freshly generated project (`fastframe
startproject`) includes `fastframe.health` and none of the others — you add
what you want, the same way you'd add any other app. This closes a
previous, deliberate-but-unwanted departure from "batteries included,
not forced": earlier versions mounted admin/auth via dedicated
`ENABLE_ADMIN`/`ENABLE_AUTH_API` settings that defaulted to `True`
(opt-out, not opt-in) inside an undocumented second app factory. That
mechanism is gone; `INSTALLED_APPS` membership is now the *only* switch.

- Admin (`fastframe.admin`) — Tailwind UI plus `/api/admin`. `GET /api/admin/schema` includes `site` from `ADMIN_SITE_TITLE` and `ADMIN_SITE_HEADER`
- Authentication / authorization (`fastframe.contrib.auth`)
- Generic REST API (`fastframe.api`)
- OpenAPI docs (`fastframe.docs`)
- Health check (`fastframe.health`) — included in a new project's `INSTALLED_APPS`
- Audit log (`fastframe.admin.audit`) — registered as a side effect of installing admin or the REST API, whichever runs first
- Background jobs (`fastframe.tasks`) — Celery, Redis by default. Needs `pip install "fast-frame[tasks]"`. See [tasks.md](tasks.md)

Note: the compiled admin UI static assets are still force-included in
every built wheel regardless of whether a project installs
`fastframe.admin` (`pyproject.toml`'s
`[tool.hatch.build.targets.wheel.force-include]`) — a separate, smaller
packaging-size concern from the *runtime* opt-in fixed above, not yet
addressed.

## Future optional components

Not yet built. These follow the same `INSTALLED_APPS` + `AppConfig`
pattern as the components above — not imported, not mounted, unless a
project explicitly installs them — to avoid the application factory
slowly becoming the monolith the [design principles](design-principles.md)
warn against:

- Templates (Jinja2) and static files for app views — next. Not an admin UI
- Caching — proposed in [ADR 0013](adr/0013-caching.md), not built
- Signals, observability helpers — planned, later

Email and object storage are not future components. [ADR 0012](adr/0012-background-jobs.md) keeps them out.

## Modularity model

```text
Core
├── API integration (application factory: get_asgi_application())
├── Configuration (settings module, INSTALLED_APPS)
├── App registry (AppConfig.ready()/get_routers()/checks()/shutdown())
├── Routing discovery (installed-app routers + ROOT_URLCONF)
└── CLI (fastframe + manage.py, including app commands)

Shipped, opt-in via INSTALLED_APPS
├── Health (fastframe.health) — on in a new project
├── Admin (fastframe.admin)
├── Auth & permissions (fastframe.contrib.auth)
├── Generic REST API (fastframe.api)
├── OpenAPI docs (fastframe.docs)
└── Background jobs (fastframe.tasks) — Celery; extra install

Always available (not gated by INSTALLED_APPS)
├── Models / ORM helpers
├── Migrations
└── Shell

Future, opt-in from the start (not yet built)
├── Templates
├── Static
├── Cache — proposed, ADR 0013, not built
└── Signals
```

Enabling/disabling any of these components — shipped or future — is
exactly the same mechanism: add or remove its dotted path in
`INSTALLED_APPS`. Nothing about a component's code runs otherwise (see
[app-contract.md](app-contract.md) for the `AppConfig.get_routers()`
hook this relies on) — a real app registry, not a set of settings
flags checked ad hoc inside the application factory.

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
│   ├── api.py             # optional FastFrameAPI (or APIRouter) named api
│   ├── urls.py            # APIRouter export
│   ├── migrations/
│   └── __init__.py
└── tests/
```

Exact names may evolve; the goal is **predictable, convention-driven** layout.
