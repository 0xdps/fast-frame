# Roadmap

Direction beyond the first release. Dates aren't fixed; scope shifts as
real usage informs priorities.

Phases below are development milestones, not package version numbers.
Everything through **Phase 4.5** is in the unreleased **v0.1.0**
candidate. Commit messages that say `v0.2.0`, `v0.3.0`, or `v0.4.0` are
pre-release working names, not package versions — see
[CHANGELOG.md](https://github.com/0xdps/fast-frame/blob/trunk/CHANGELOG.md). After `0.1.0` is released, fixes bump
the patch version and a new feature bumps the minor version. Phase 5
has not started.

| Phase | Theme | Status |
| --- | --- | --- |
| Phase 1 | Core loop — `startproject` → `manage.py` → migrate → shell | ✅ Shipped (v0.1.0) |
| Phase 2 | Developer experience polish | ✅ Shipped (v0.1.0) |
| Phase 3 | Admin, relationships, session auth | ✅ Shipped (v0.1.0) |
| Phase 4 | Harden auth & authorization | ✅ Shipped (v0.1.0) |
| Phase 4.5 | App registry for batteries + richer ORM | ✅ Shipped (v0.1.0) |
| Phase 5 | Templates and static files | 🔜 Next |
| Phase 6+ | Additional batteries (tasks, cache, email, storage, …) | 📋 Planned |
| Phase 7 | Production-ready platform | 📋 Planned |

## Phase 1 — Core loop ✅

`startproject`, `manage.py` (`runserver`, `migrate`, `shell`, `test`, `startapp`), thin models with a chainable `QuerySet`, Alembic migrations. Validated end-to-end against a real app (`examples/todo_app`).

## Phase 2 — Developer experience ✅

`check` / `check --database`, `showmigrations`, `dbshell`, app lifecycle hooks (`AppConfig.checks()` / `shutdown()`), `.env` support, a pagination dependency, and test utilities (`fastframe.testing.override_settings`).

## Phase 3 — Admin, relationships, session auth ✅

- **Declarative fields** (`fields.CharField`, `IntegerField`, `BooleanField`, `DateTimeField`, `DecimalField`, `EmailField`, `URLField`, `UUIDField`, `JSONField`, …) — see [models-fields-design.md](models-fields-design.md).
- **Auto relationships**: `ForeignKey` and `ManyToManyField` (incl. self-referential) generate their SQLAlchemy `relationship()`/join tables automatically; Django-style `RelatedList` helpers (`.add()`, `.remove()`, `.set()`, `.clear()`, `.all()`).
- **Admin**: REST API (`get_admin_api_router()`) + a bundled React admin UI (react-admin) built on top of it. The admin is **React-only** — an SSR/Jinja2 mode was tried (see [ADR 0007](adr/0007-ssr-for-admin-v0-3.md)) and replaced by the REST + React approach (see [ADR 0008](adr/0008-rest-api-react-admin.md)); the SSR code path has since been removed entirely.
- **Session authentication**: signed-cookie login/logout for the admin, always required (`can_access_admin` — no setting disables it), plus a built-in `User` model with password hashing. Details and current gaps: [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md).
- **Generic REST API**: token-authenticated CRUD (`/api/v1/{resource}`) over the same registered models, for non-browser clients (mobile apps, scripts, integrations). Opt in by adding `"fastframe.api"` to `INSTALLED_APPS` (Phase 4.5). There is no `ENABLE_REST_API` setting.
- **Audit log**: every create/update/delete through either surface is recorded in `AuditLog` (who, what, when, old→new values), viewable read-only in the admin.

## Phase 4 — Harden auth & authorization ✅

Closed most of the gaps called out in [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md):

- **Fine-grained, per-request permissions**: Django-style permission strings
  (`"blog.change_post"`) on a new `Group` model and `User.permissions`/
  `User.groups`; `ModelAdmin.enforce_permissions` opts a model in to
  per-request `has_*_permission` checks (default stays static/backward
  compatible). `readonly_fields`/`fields`/`exclude` are now actually
  enforced on create/update, not just used for UI rendering. See
  [permissions.md](permissions.md).
- **General-purpose auth/authz usable outside `/admin`**: `POST
  /api/auth/login` / `/logout` / `GET /api/auth/me`, plus
  `login_required`/`get_current_user`/`permission_required` FastAPI
  dependencies — all sharing the same signed session cookie as the admin.
  See [auth.md](auth.md#general-purpose-session-auth-outside-admin).
- **Rate limiting** on `/api/admin/login`, `/api/auth/login`, and
  `/api/auth/token` — in-memory sliding window + lockout, swappable
  backend interface for later. See [settings.md](settings.md#rate-limiting).
- **Session revocation**: `User.invalidate_sessions()` bumps a
  `session_version` embedded in the cookie, invalidating every previously
  issued session for that user without a session table.
- **Timing-safe authentication**: constant-time password hash comparison;
  `authenticate()` performs a dummy hash comparison for unknown/inactive
  usernames to avoid leaking which usernames exist via response timing.
- **Password strength policy**: `PASSWORD_MIN_LENGTH`, rejects
  username-as-password, on by default in `User.set_password()`.
- **Token expiry**: opt-in `API_TOKEN_DEFAULT_EXPIRY_DAYS` / per-token
  `expires_in_days` for `/api/auth/token`.
- **`MIDDLEWARE` setting wired up**, plus built-in, opt-in CORS
  (`CORS_ALLOWED_ORIGINS`) and on-by-default security headers
  (`SECURE_HEADERS`) — previously `MIDDLEWARE` was declared but never
  applied by `create_app()`.

**Deferred to a later release:** `ManyToManyField(through=...)` (custom
columns on a join table) and CSRF tokens beyond the existing
`SameSite=Lax` mitigation — see [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md)
for the up-to-date list of what's still open.

## Phase 4.5 — App registry for batteries + richer ORM ✅

- **Batteries mount via `INSTALLED_APPS`, not `ENABLE_*` settings**: admin
  (`fastframe.admin`), general auth (`fastframe.contrib.auth`), and the
  generic REST API (`fastframe.api`) now expose an `AppConfig` (`ready()`
  + `get_routers()`) and are mounted purely by being listed in
  `INSTALLED_APPS` — exactly like adding any other app. The
  `ENABLE_ADMIN`/`ENABLE_AUTH_API`/`ENABLE_REST_API` settings are gone. A
  freshly generated project doesn't install any of them by default
  (previously admin and general auth defaulted to *on*, opt-out rather
  than opt-in). See [app-contract.md](app-contract.md), [settings.md](settings.md#enabling-admin-auth-and-the-rest-api).
- **One application factory**: `get_asgi_application()` (previously
  `ROOT_URLCONF` routers + DB session middleware only) now also applies
  `MIDDLEWARE`/CORS/security headers and mounts every installed app's
  routers — everything `create_app()` used to do, plus what
  `get_asgi_application()` always did. `create_app()` is now a thin,
  deprecated alias for it.
- **Richer ORM, still "thin layer + escape hatch to SQLAlchemy," not a
  second query-algebra**: `F()` field-reference expressions are wired up
  end-to-end (`.filter(karma__gt=F("num_posts"))`, atomic
  `user.karma = F("karma") + 1; user.save()` — previously present as
  classes but non-functional); `select_related()`/`prefetch_related()`
  eager loading (the direct answer to the classic N+1 query trap);
  `bulk_create()`/`bulk_update()` and queryset-level `.update()`/
  `.delete()`; `get_or_create()`/`update_or_create()`; `values()`/
  `values_list()` projections that skip full model instantiation;
  `only()`/`defer()` partial column loading; an `atomic()`
  transaction/SAVEPOINT helper. `Q()` objects and Django-style field
  lookups (`__gte`, `__icontains`, …) already worked and are now
  documented. Deliberately **not** added, and not planned:
  `annotate()`/subquery composition/window functions — see
  [orm-features.md](orm-features.md) and [design-principles.md](design-principles.md).
- **Migrations fix**: per-app migration directory discovery now skips
  dotted, framework-provided app names (e.g. `fastframe.contrib.auth`)
  instead of trying to create a literal directory named that at the
  project root.

## Phase 5 — Templates and static files 🔜

- Jinja2 templates and discovery for app-defined views (independent of the admin, which stays React-only)
- Static file handling and `collectstatic` for production

## Phase 6+ — Additional batteries 📋

Background tasks, email, caching, storage (unlocks `FileField`/`ImageField`), signals/events, custom management commands ecosystem, observability, production checks, deployment helpers.

## Phase 7 — Production-ready platform 📋

Stable public API, migration story, documentation, and operational commands (`check --deploy`, `migrate`, `collectstatic`) that teams trust for production.
