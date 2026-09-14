# App contract (draft)

This document defines how **installed apps** extend a FastFrame project. It is a design draft until v0.1 implementation locks the API.

## Purpose

Django's long-term strength is extensibility: third-party packages install as apps and contribute models, routes, and commands. FastFrame adopts that **shape**, not Django's full feature set.

## Settings

Projects declare apps in settings (exact module path TBD), e.g.:

```python
INSTALLED_APPS = [
    "fastframe.contrib.orm",  # example built-in contrib name
    "users",
    "billing",
]
```

Order may matter for discovery and migrations; rules TBD.

## App package layout (convention)

Each app is a Python package. Conventional files FastFrame **may** auto-discover:

| File / symbol | Purpose |
| --- | --- |
| `apps.py` → `AppConfig` subclass | Metadata and `ready()` hook |
| `models.py` | ORM models for migration discovery |
| `urls.py` → `router` | FastAPI `APIRouter` to mount |
| `management/commands/` | Custom `manage.py` commands |
| `checks.py` | Registrations for `manage.py check` (later) |

Apps **must not** be required to implement every file. Missing modules are skipped.

## AppConfig (draft)

```python
# users/apps.py (illustrative — not implemented)
class UsersConfig(AppConfig):
    name = "users"
    label = "users"

    def ready(self) -> None:
        # import side effects, register hooks, etc.
        ...
```

Open questions:

- Default `AppConfig` if only `users/__init__.py` exists?
- Auto-created `apps.py` from `startapp` template?

## Router discovery

- Each app may expose `router = APIRouter()` from `urls.py` (or a named export — TBD).
- Project `config/urls.py` aggregates routers or delegates to framework auto-discovery.

**Non-goal:** a Django URLconf dispatcher with regex paths.

## Models and migrations

- Models live in `models.py` (or documented split modules later).
- Migration autogenerate collects metadata from all installed apps.
- App label influences migration file naming (Alembic revision layout TBD).

## Management commands

Custom commands live under `app/management/commands/<name>.py` (Django-familiar path) unless we choose a flatter layout in implementation.

## Third-party apps

A distributable app is a normal Python package that:

1. Declares itself in `INSTALLED_APPS`.
2. Optionally ships models, router, commands, and `AppConfig`.

Versioning of the app contract will be documented when v0.1 ships; breaking changes require ADRs.

## Contrib vs third-party

- **`fastframe.contrib.*`**: maintained in this repository, optional to enable.
- **Third-party**: PyPI packages; same contract as first-party apps.

## Proof point for v0.2

Before building admin, ship a tiny contrib app (e.g. health check router + `check` subcommand) to validate the contract.
