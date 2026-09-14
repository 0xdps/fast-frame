# Non-goals

Explicit boundaries help keep FastFrame coherent. This list applies especially to **v0.1**; some items may become optional apps later.

## Not a Django clone

- No requirement to match Django APIs for compatibility.
- No goal to reimplement Django admin, auth, forms, templates, or CBVs in core.

## Not replacing FastAPI at the HTTP layer

- No Django-style function or class-based views.
- No parallel request/response abstraction when FastAPI + Pydantic already fit.
- FastAPI tutorials should largely apply inside FastFrame apps.

## Not a second ORM

- The thin manager is **convenience on SQLAlchemy**, not a hidden query language.
- No promise to support every Django ORM feature via `objects.*`.
- Complex queries, locking, window functions, and advanced loading → SQLAlchemy.

## Not hiding SQLAlchemy forever

- Models should remain recognizable as SQLAlchemy mapped classes.
- Public docs will show the escape hatch early.

## Not a cloud or hosting platform

- Conventional ASGI deployment only in early releases.
- Helpers for Docker/K8s may come much later; they are not core.

## Not interactive architecture at project creation

- `startproject` must not begin with a questionnaire about stack choices.
- Sensible defaults first; customization later.

## Not wrapper proliferation (initially)

- No FastFrame-branded `APIRouter`, `Query`, or SQLAlchemy `select` unless proven necessary.
- Integration wrappers only: app factory, session dependency, model discovery, migrations, CLI.

## Deferred features (not rejected forever)

| Feature | Intent |
| --- | --- |
| Admin | Optional app, Django-admin-like UX |
| Auth | Optional app |
| Templates / static | Optional; Jinja2 likely |
| Signals | Only if hooks + `ready()` are insufficient |
| Full backend protocols | Auth/storage/cache backends after second implementations exist |
