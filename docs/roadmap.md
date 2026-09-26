# Roadmap

Direction beyond v0.1. Dates aren't fixed; scope shifts as real usage informs priorities.

| Version | Theme | Status |
| --- | --- | --- |
| v0.1 | Core loop — `startproject` → `manage.py` → migrate → shell | ✅ Shipped |
| v0.2 | Developer experience polish | ✅ Shipped |
| v0.3 | Admin, relationships, session auth | ✅ Shipped |
| v0.4 | Harden auth & authorization | 🔜 Next |
| v0.5 | Templates and static files | 📋 Planned |
| v0.6+ | Additional batteries (tasks, cache, email, storage, …) | 📋 Planned |
| v1.0 | Production-ready platform | 📋 Planned |

## v0.1 — Core loop ✅

`startproject`, `manage.py` (`runserver`, `migrate`, `shell`, `test`, `startapp`), thin models with a chainable `QuerySet`, Alembic migrations. Validated end-to-end against a real app (`examples/todo_app`).

## v0.2 — Developer experience ✅

`check` / `check --database`, `showmigrations`, `dbshell`, app lifecycle hooks (`AppConfig.checks()` / `shutdown()`), `.env` support, a pagination dependency, and test utilities (`fastframe.testing.override_settings`).

## v0.3 — Admin, relationships, session auth ✅

- **Declarative fields** (`fields.CharField`, `IntegerField`, `BooleanField`, `DateTimeField`, `DecimalField`, `EmailField`, `URLField`, `UUIDField`, `JSONField`, …) — see [models-fields-design.md](models-fields-design.md).
- **Auto relationships**: `ForeignKey` and `ManyToManyField` (incl. self-referential) generate their SQLAlchemy `relationship()`/join tables automatically; Django-style `RelatedList` helpers (`.add()`, `.remove()`, `.set()`, `.clear()`, `.all()`).
- **Admin**: REST API (`get_admin_api_router()`) + a bundled React admin UI (react-admin) built on top of it. The admin is **React-only** — an SSR/Jinja2 mode was tried (see [ADR 0007](../adr/0007-ssr-for-admin-v0-3.md)) and replaced by the REST + React approach (see [ADR 0008](../adr/0008-rest-api-react-admin.md)); the SSR code path has since been removed entirely.
- **Session authentication**: signed-cookie login/logout for the admin (`ADMIN_REQUIRE_AUTH`, `can_access_admin`), plus a built-in `User` model with password hashing. Details and current gaps: [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md).

## v0.4 — Harden auth & authorization 🔜

Closing the gaps called out in [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md):

- Fine-grained, per-request permissions (per-model, per-field) — replacing the static `has_*_permission` booleans on `ModelAdmin`
- CSRF protection for session cookies
- Rate limiting on `/api/admin/login`
- Audit logging for admin actions
- General-purpose auth/authz usable outside `/admin` — login/session dependencies for regular app routes, groups/roles, FastAPI middleware
- `ManyToManyField(through=...)` — custom columns on the join table (deferred from v0.3)

## v0.5 — Templates and static files 📋

- Jinja2 templates and discovery for app-defined views (independent of the admin, which stays React-only)
- Static file handling and `collectstatic` for production

## v0.6+ — Additional batteries 📋

Background tasks, email, caching, storage (unlocks `FileField`/`ImageField`), signals/events, custom management commands ecosystem, observability, production checks, deployment helpers.

## v1.0 — Production-ready platform 📋

Stable public API, migration story, documentation, and operational commands (`check --deploy`, `migrate`, `collectstatic`) that teams trust for production.
