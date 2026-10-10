# App contract

This document defines how **installed apps** extend a FastFrame project. Most of what was originally a design draft is now locked in as of v0.1/v0.2; remaining open items are called out explicitly below.

## Purpose

Django's long-term strength is extensibility: third-party packages install as apps and contribute models, routes, and commands. FastFrame adopts that **shape**, not Django's full feature set.

## Settings

**Module path (decided):** settings live in an ordinary, importable Python module — `config.settings` by default (set via the `FASTFRAME_SETTINGS_MODULE` env var, which the generated `manage.py` sets with `os.environ.setdefault(...)`, or passed explicitly to `bootstrap()`/`get_asgi_application()`). It's just `importlib.import_module(module_name)` — no special settings object or metaclass.

Projects declare apps in settings, e.g.:

```python
INSTALLED_APPS = [
    "fastframe.contrib.orm",  # example built-in contrib name
    "users",
    "billing",
]
```

**Order is preserved and matters:** `populate_apps()` processes `INSTALLED_APPS` in list order and appends to `AppsRegistry.app_configs` in that same order. `AppConfig.ready()` hooks run in that order at bootstrap; `AppConfig.shutdown()` hooks (see below) run in that same order at ASGI shutdown. If app B's `ready()` depends on app A having already run its setup, list A first.

**`.env` files (v0.2):** before importing the settings module, FastFrame loads a `.env` file (if present, found by searching upward from the current working directory) into `os.environ` via `python-dotenv` — without overriding variables already set in the real environment. Generated projects ship a `.env.example` (checked in) and `.gitignore` the real `.env`. This only helps if your settings module reads values via `os.environ.get(...)` (the generated `config/settings.py` does, for `DEBUG` and `DATABASE_URL`) — FastFrame doesn't otherwise interpret `.env` contents itself.

**Splitting settings by environment:** no special support or convention is enforced — `FASTFRAME_SETTINGS_MODULE` accepts *any* importable module path, so `config.settings.dev` / `config.settings.prod` (each importing shared values from a `config.settings.base`) works today with zero framework changes. Not scaffolded by default, to keep the single-`settings.py` starting point simple; adopt it when a project actually needs it.

## App package layout (convention)

Each app is a Python package. Conventional files FastFrame **may** auto-discover:

| File / symbol | Purpose |
| --- | --- |
| `apps.py` → `AppConfig` subclass | Metadata and `ready()` hook |
| `models.py` | ORM models for migration discovery |
| `tasks.py` | Celery tasks, imported when `fastframe.tasks` is installed |
| `api.py` → `api` | `FastFrameAPI` (or a native `APIRouter`) mounted for this app |
| `urls.py` → `router` | FastAPI `APIRouter`, aggregated by `config/urls.py` |
| `management/commands/<name>.py` | A `manage.py` command named `<name>` |
| `AppConfig.checks()` | Hook returning `list[CheckMessage]` for `manage.py check` |

Apps **must not** be required to implement every file. Missing modules are skipped.

## AppConfig

```python
# users/apps.py
class UsersConfig(AppConfig):
    name = "users"
    label = "users"

    def ready(self) -> None:
        # import side effects, register hooks, etc.
        ...

    def shutdown(self) -> None:
        # cleanup on ASGI app shutdown (not called for CLI commands)
        ...

    def checks(self) -> list[CheckMessage]:
        # return CheckMessage(level=WARNING, message="...") entries;
        # see fastframe.core.checks
        ...

    def get_routers(self) -> list[APIRouter]:
        # return routers built programmatically from settings, instead of
        # (or in addition to) the static urls.py -> router convention below
        ...

    def shell(self, context: dict) -> None:
        # optional: mutate manage.py shell's local namespace in place.
        # Not a method on the AppConfig base class — fastframe.shell calls
        # it via getattr(app_config, "shell", None), so it's opt-in per
        # app. See docs/shell.md.
        ...
```

`ready()`, `shutdown()`, `checks()`, and `get_routers()` are base-class
methods with no-op defaults — override only the ones an app needs.
`shell()` is duck-typed, not declared on the base class; define it only
on apps that want to contribute to the shell namespace.

Resolved:

- **Default `AppConfig` if only `users/__init__.py` exists?** Yes — `populate_apps()` falls back to a bare `AppConfig` (name/label inferred from the app's module path) if `<app>.apps` doesn't exist or has no `AppConfig` subclass.
- **Auto-created `apps.py` from `startapp` template?** Yes — `manage.py startapp <name>` always generates one.

## Router discovery

Three mechanisms, all mounted by `get_asgi_application()`, in this order:

1. **`AppConfig.get_routers()`.** Override this to return routers built at mount time, when the shape depends on settings. The factory collects these in `INSTALLED_APPS` order, after every app's `ready()` has run.
2. **`<app>.api` → `api`.** An installed app may export `api = FastFrameAPI()` from `api.py`. FastFrame mounts `api.router`. A native `APIRouter` assigned to the same name is mounted too. A missing `api.py` is normal. The path is never inferred from a class name. See [API](api-layer.md).
3. **`urls.py` → `router`.** Each app may expose `router = APIRouter()` from `urls.py`. `manage.py startapp` scaffolds this, and `add_router_to_urls()` wires it into `config/urls.py`. The app factory mounts that list last, after both of the above.

A literal path registered earlier wins over a catch-all registered later (FastAPI/Starlette match routes in registration order) — this is why, for example, `fastframe.admin`'s `get_routers()` mounts its auth router before its `/{resource}` CRUD router.

This is also what makes FastFrame's own batteries opt-in: `fastframe.admin`, `fastframe.contrib.auth`, `fastframe.api`, and `fastframe.docs`. Their code runs only when listed in `INSTALLED_APPS`. There is no `ENABLE_*` setting for turning one on. `fastframe.docs` is the switch for `/docs`, `/redoc`, and `/openapi.json`. See [architecture.md](https://github.com/0xdps/fast-frame/blob/trunk/docs/architecture.md).

**Non-goal:** a Django URLconf dispatcher with regex paths.

## Models and migrations

- Models live in `models.py` (or documented split modules later).
- Migration autogenerate collects metadata from all installed apps.
- **Revision layout:** each project app owns its migration files. `makemigrations` writes only that app's table operations into `<app>/migrations/versions`. Framework apps (`fastframe.contrib.auth`, `fastframe.admin`, and any other dotted installed app) are not a directory in the project, so their operations go to `config/migrations/versions` instead of being appended to whichever local app is listed first. When several apps change at once, the new files are chained in that order (framework, then `INSTALLED_APPS`) so later tables can reference earlier ones. `showmigrations` prints the list grouped by owning app.

## Management commands

An installed app registers commands under `<app>/management/commands/<name>.py`. The module name is the command name. `execute(args)` is required. `add_arguments(parser)` is optional and receives the command's argument parser. The same shape is what FastFrame's own commands use.

FastFrame imports these modules while building `manage.py`'s command list. A missing `management` package is skipped. A name that matches a built-in command, or the same name in two installed apps, is an error. See [cli.md](cli.md#app-commands).

## Third-party apps

A distributable app is a normal Python package that:

1. Declares itself in `INSTALLED_APPS`.
2. Optionally ships models, router, commands, and `AppConfig`.

Versioning of the app contract will be documented when v0.1 ships; breaking changes require ADRs.

## Contrib vs third-party

- **`fastframe.contrib.*`**: maintained in this repository, optional to enable.
- **Third-party**: PyPI packages; same contract as first-party apps.

## Proof point for v0.2 — done

The built-in `fastframe.health` app (listed in every generated project's
`INSTALLED_APPS`) validated the router half of the contract end-to-end: a
router mounted purely via `AppConfig.get_routers()`, with nothing
reachable unless the app is actually installed. (`HealthConfig` does not
override `checks()` — for that half of the contract, see
`fastframe.tasks`'s `tasks.E001` check, in `src/fastframe/tasks/apps.py`.)
Before building admin (v0.3), this is the pattern third-party apps should
follow.
