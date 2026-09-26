# Roadmap

Direction beyond the first release. Dates aren't fixed; scope shifts as
real usage informs priorities.

Phases below are development milestones, not package version numbers —
they don't map 1:1 onto `fastframe`'s actual semver release (see
[CHANGELOG.md](../CHANGELOG.md)). Everything through **Phase 4** shipped
together as **v0.1.0**, the first tagged release. From here, releases
follow standard semver: fixes bump the patch version, new features bump
the minor version.

| Phase | Theme | Status |
| --- | --- | --- |
| Phase 1 | Core loop — `startproject` → `manage.py` → migrate → shell | ✅ Shipped (v0.1.0) |
| Phase 2 | Developer experience polish | ✅ Shipped (v0.1.0) |
| Phase 3 | Admin, relationships, session auth | ✅ Shipped (v0.1.0) |
| Phase 4 | Harden auth & authorization | ✅ Shipped (v0.1.0) |
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
- **Admin**: REST API (`get_admin_api_router()`) + a bundled React admin UI (react-admin) built on top of it. The admin is **React-only** — an SSR/Jinja2 mode was tried (see [ADR 0007](../adr/0007-ssr-for-admin-v0-3.md)) and replaced by the REST + React approach (see [ADR 0008](../adr/0008-rest-api-react-admin.md)); the SSR code path has since been removed entirely.
- **Session authentication**: signed-cookie login/logout for the admin, always required (`can_access_admin` — no setting disables it), plus a built-in `User` model with password hashing. Details and current gaps: [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md).
- **Generic REST API**: `ENABLE_REST_API` opts in to token-authenticated CRUD (`/api/v1/{resource}`) over the same registered models, for non-browser clients (mobile apps, scripts, integrations).
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

## Phase 5 — Templates and static files 🔜

- Jinja2 templates and discovery for app-defined views (independent of the admin, which stays React-only)
- Static file handling and `collectstatic` for production

## Phase 6+ — Additional batteries 📋

Background tasks, email, caching, storage (unlocks `FileField`/`ImageField`), signals/events, custom management commands ecosystem, observability, production checks, deployment helpers.

## Phase 7 — Production-ready platform 📋

Stable public API, migration story, documentation, and operational commands (`check --deploy`, `migrate`, `collectstatic`) that teams trust for production.
