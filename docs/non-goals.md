# Non-goals

Explicit boundaries help keep FastFrame coherent. They still hold. Some rows in the last table have since shipped as optional apps; that table says which.

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
- Eager loading of declared relations (`select_related()`, `prefetch_related()`) is in the thin layer. Locking, window functions, `annotate()`, and subquery composition stay SQLAlchemy. A new ORM method past the list in [ADR 0003](adr/0003-thin-orm-with-sqlalchemy-escape-hatch.md) needs a superseding ADR, not a feature-page edit.

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

| Feature | Now |
| --- | --- |
| Admin | Shipped as `fastframe.admin`. Still not part of core. The UI is the bundled Tailwind app, not React Admin — see the Addition on [ADR 0008](adr/0008-rest-api-react-admin.md) |
| Auth | Shipped as `fastframe.contrib.auth`. Still not part of core |
| Templates / static | Not started. Phase 5. Jinja2 for app views; the admin stays React-only |
| Signals | Still deferred. Only if hooks and `ready()` are insufficient |
| Full backend protocols | Still deferred. Auth, storage, and cache backends after a second implementation exists |
| CSRF tokens, per-object permissions, `ManyToManyField(through=...)` | Still deferred. See [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md) |
