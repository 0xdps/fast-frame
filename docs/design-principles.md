# Design principles

## 1. Zero-decision start

A developer should create and run an application immediately:

```text
fastframe startproject myproject
cd myproject
python manage.py runserver
```

Advanced configuration comes later; the first path stays simple.

## 2. Batteries included, not batteries forced

FastFrame provides first-party solutions (models, migrations, shell, CLI) without requiring every app to use admin, templates, sessions, auth, or static files.

Optional capabilities should plug in as **apps** or **components**, not as mandatory core.

## 3. Convention over configuration

Common applications need little configuration. Sensible defaults beat exhaustive option surfaces in early releases.

## 4. Hide unnecessary complexity

Developers should not need to understand how FastAPI, SQLAlchemy, Alembic, and Uvicorn are wired together for a **normal** FastFrame project.

They **should** be able to use those libraries directly when the framework's thin layer is not enough.

## 5. Familiar where it helps

Django developers should recognize:

- `manage.py`
- models, migrations, shell
- apps and settings

FastFrame is **not** constrained by Django compatibility. Names and workflow overlap are intentional; behavior may differ where FastAPI or SQLAlchemy offer a better path.

## 6. Production-minded

Eventually support a clear path:

```text
development → testing → staging → production
```

Examples: `check --deploy`, migrate, collectstatic (when static files exist). Deployment remains conventional (Docker, K8s, VMs, managed ASGI) — not a bundled cloud platform in v0.1.

## 7. Composable architecture

Capabilities should be independently replaceable or extensible where practical. Internal modularity should not collapse into a monolith just because the UX feels “Django-like.”

## 8. Wrap integration, not identity

Thin wrappers belong where FastFrame **owns lifecycle** (app factory, session dependency, model discovery, migrations, CLI).

Do **not** rebrand FastAPI routers or SQLAlchemy query APIs without a proven, repeated need. Re-exports are fine; shadow APIs are costly.

## 9. Extensibility over feature cloning

Copy Django's **extension model** (installed apps, hooks, commands), not every built-in feature. Admin, auth, and templates can arrive as optional apps once the contract is stable.
