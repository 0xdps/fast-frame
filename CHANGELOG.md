# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-09-26

Auth hardening release. Closes out `docs/roadmap.md`'s "v0.4 — Harden auth
& authorization": opt-in, per-request permissions (`Group`, permission
strings), general-purpose session auth for non-admin routes, rate
limiting, session revocation, CORS/security headers, and several
timing/validation fixes. Full details: [docs/permissions.md](docs/permissions.md),
[docs/auth.md](docs/auth.md), [docs/ADMIN_SECURITY_WARNING.md](docs/ADMIN_SECURITY_WARNING.md).

### Added

- **Permissions** (`fastframe.contrib.auth.permissions`, new `Group`
  model): Django-style permission strings (`"blog.change_post"`) on
  `User.permissions` and `Group.permissions`, with `User.groups`
  (many-to-many). `ModelAdmin.enforce_permissions` (default `False`, fully
  backward compatible) opts a model in to per-request `has_*_permission`
  checks resolved against the current user's effective permissions;
  superusers always pass, and an explicit `has_*_permission = False`
  remains a hard override even for matching permissions. New
  `get_has_view_permission`/`get_has_add_permission`/
  `get_has_change_permission`/`get_has_delete_permission(user)` methods on
  `ModelAdmin` back every admin API and REST API route now. See
  [docs/permissions.md](docs/permissions.md).
- **`readonly_fields`/`fields`/`exclude` are now enforced on write**:
  previously used only for admin UI rendering, these now actually filter
  create/update payloads (`ModelAdmin.get_editable_fields`) — a client can
  no longer set a field marked read-only just by including it in the
  request body. The schema now also marks these fields `"readOnly": true`.
- **Missing permission check on `list`/`choices` fixed**: `list_records`
  and `fk_choices` in the admin/REST API previously performed **no**
  permission check at all, regardless of `has_view_permission`. Both now
  enforce it like every other route.
- **General-purpose session auth** (`fastframe.contrib.auth.views`,
  `fastframe.contrib.auth.dependencies`): `POST /api/auth/login`, `POST
  /api/auth/logout`, `GET /api/auth/me` (opt-out via `ENABLE_AUTH_API =
  False`), independent of `can_access_admin` and sharing the same signed
  session cookie as the admin. New FastAPI dependencies for any app
  router: `get_current_user`, `login_required`, `permission_required(perm)`.
  See [docs/auth.md](docs/auth.md#general-purpose-session-auth-outside-admin).
- **Session revocation**: `User.session_version` (embedded in the signed
  session cookie payload) plus `User.invalidate_sessions()` — bumping it
  invalidates every previously issued cookie for that user immediately,
  without a session table.
- **Rate limiting** (`fastframe.core.ratelimit`): in-memory sliding-window
  limiter with lockout, applied to `/api/admin/login`, `/api/auth/login`,
  and `/api/auth/token` (`RATE_LIMIT_LOGIN_*` settings; `429` +
  `Retry-After` when locked out). Single-process only by design — meant
  to blunt naive brute-forcing, not a distributed production limiter.
- **CORS + security headers + working `MIDDLEWARE` setting**
  (`fastframe.middleware.security.SecurityHeadersMiddleware`,
  `fastframe.core.app._apply_middleware`): `MIDDLEWARE` (dotted paths) is
  now actually applied by `create_app()` — previously declared in
  settings but never wired up. `SECURE_HEADERS` (default `True`) adds
  `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` always,
  and `Strict-Transport-Security` when `DEBUG = False`. `CORS_ALLOWED_ORIGINS`
  (default `[]`, disabled) opts in to Starlette's `CORSMiddleware`.
- **Token expiry**: `Token.expires_at` (nullable), `API_TOKEN_DEFAULT_EXPIRY_DAYS`
  setting, and an optional `expires_in_days`/`expiresInDays` argument to
  `create_token()`/`POST /api/auth/token`. An expired token is rejected
  exactly like a revoked one.
- **Password strength policy** (`fastframe.contrib.auth.validators`):
  `User.set_password()` now validates length (`PASSWORD_MIN_LENGTH`,
  default `8`) and rejects a password equal to the username, before
  hashing. `validate=False` remains available as an escape hatch.

### Fixed

- **Timing-safe authentication**: `check_password()` now compares hashes
  with `hmac.compare_digest` instead of `==`; `authenticate()` always
  performs a full dummy-hash comparison for unknown or inactive
  usernames, closing a timing side-channel that previously let response
  time reveal whether a username exists.
- **`fastframe.api.auth`'s stale, duplicate `_snapshot_user`**: didn't
  include `permissions`/`is_superuser`, so every permission check on the
  REST API surface silently evaluated against an empty permission set.
  Now imports the shared `snapshot_user` from
  `fastframe.contrib.auth.dependencies`.
- **Three pre-existing framework bugs**, uncovered while adding the first
  genuine forward-referenced many-to-many relationship (`User.groups` →
  `Group`, defined later in the same module) — none specific to this
  feature, but all silently masked until now:
  - `models/base.py`: the SQLAlchemy `before_configured` event listener
    that resolves deferred forward-referenced FK/M2M targets was
    registered on `Model` (a mapped class) instead of `Mapper` (the
    actual required global-event target) — it never fired. Every prior
    FK/M2M test happened to define its target class before the
    referencing class, so eager resolution always succeeded and this dead
    code path went unexercised.
  - `core/bootstrap.py`: `bootstrap()` now calls
    `sqlalchemy.orm.configure_mappers()` after all apps' `.ready()` hooks
    run, so deferred relationships (like the one above) are resolved
    — and their join tables registered in `Model.metadata` — before any
    caller's subsequent `Model.metadata.create_all()`.
  - `models/fields.py`: `JSONField` now wraps its SQLAlchemy type in
    `sqlalchemy.ext.mutable.MutableDict`/`MutableList` when its `default`
    is `dict`/`list`. Without this, in-place mutations
    (`user.user_data["key"] = value`) were invisible to SQLAlchemy's
    dirty-tracking and silently failed to persist on `UPDATE` (the
    initial `INSERT` was unaffected) — this had been silently broken for
    every `JSONField` with a mutable default since it was introduced.

### Changed

- Package version bumped to `0.4.0`.

## [0.3.1] - 2026-09-26

### Added

- **Generic REST API** (`fastframe.api`, opt-in via `ENABLE_REST_API`):
  token-authenticated CRUD (`GET/POST/PUT/DELETE /api/v1/{resource}`,
  `/api/v1/schema`, `/api/v1/{resource}/choices/{field}`) over the same
  models registered with `admin_site` — for non-browser clients that can't
  carry a session cookie. `POST /api/auth/token` exchanges
  username/password for an opaque bearer token (`secrets.token_hex(32)`,
  stored only as its SHA-256 hash, shown once); `DELETE /api/auth/token`
  revokes it. Any active user (not just `can_access_admin`) may
  authenticate; per-model permissions still come from the shared
  `ModelAdmin.has_*_permission` flags. `ENABLE_REST_API_DOCS` and
  `API_PREFIX` (default `/api/v1`) round out the settings. Internally, the
  admin API and this new API now share one CRUD implementation
  (`fastframe.admin.api._build_crud_router`), parameterized by which auth
  dependency guards it. See [docs/rest-api.md](docs/rest-api.md).
- **Audit log** (`fastframe.admin.audit.AuditLog`): every create, update,
  and delete made through the admin API or the new REST API is recorded —
  who, what (model, object id/repr), when, which surface (`source`:
  `"admin"`/`"api"`), and the changed values (full snapshot for
  create/delete, changed-fields-only diff for update). Read-only,
  browsable in the admin UI like any other model. See the "Audit Logging"
  section of
  [docs/ADMIN_SECURITY_WARNING.md](docs/ADMIN_SECURITY_WARNING.md).

### Removed

- **`ADMIN_REQUIRE_AUTH` setting**: admin authentication is now always
  required — there is no way to disable it, even for local development.
  Every `/api/admin/*` route always requires a valid session. See
  [docs/ADMIN_SECURITY_WARNING.md](docs/ADMIN_SECURITY_WARNING.md).
- **SSR admin mode** (`ADMIN_MODE = "ssr"`): the Jinja2-templated,
  server-rendered admin views (`admin_index`, `model_list`, `model_add`,
  `model_detail`) and their templates have been removed. The admin UI is now
  React-only — `ADMIN_MODE` only selects which React build to serve
  (`"static"`, the bundled default, or `"custom"`, a project-built one via
  `manage.py startadmin`). Any other/unrecognized `ADMIN_MODE` value now
  falls back to `"static"` instead of erroring or serving SSR. The `jinja2`
  dependency was dropped as a result — nothing in `fastframe` imports it
  anymore.
- Removed one-off session/audit/progress markdown files that had
  accumulated at the repo root and in `docs/` (`SUMMARY.md`,
  `V03_SUMMARY.md`, `docs/ACHIEVEMENTS_SUMMARY.md`,
  `docs/ACTION_PLAN_V0.3.md`, `docs/ADMIN_COMPLETION_SUMMARY.md`,
  `docs/AUDIT_2026_09_23.md`, `docs/IMPLEMENTATION_SUMMARY.md`,
  `docs/IMPROVEMENTS_CATALOG.md`, `docs/RELATIONSHIP_AUTO_GEN_COMPLETE.md`,
  `docs/SESSION_FINAL_SUMMARY.md`, `docs/v0.3-progress.md`,
  `docs/admin-crud-implementation-plan.md`, `docs/blog-app-restructuring.md`)
  along with `docs/admin-quick-reference.md`, a stale duplicate of
  `docs/admin-setup.md`. Their content is superseded by this changelog,
  `README.md`, and the living guides indexed in `docs/README.md`.

## [0.3.0] - 2026-09-26

Admin release. Adds a Django-style declarative field API, automatic
relationship generation (`ForeignKey` and `ManyToManyField`), and a full
admin system — REST API + bundled React UI — protected by session-based
authentication by default.

### Added

- **Declarative fields** (`fastframe.models.fields`): `CharField`, `TextField`,
  `IntegerField`, `BigIntegerField`, `SmallIntegerField`, `BooleanField`,
  `FloatField`, `DateField`, `DateTimeField` (`auto_now`/`auto_now_add`),
  `DecimalField`, `EmailField`, `URLField`, `UUIDField` (UUID v7 by default),
  `JSONField`, `AutoField`/`BigAutoField`, replacing raw `mapped_column()`
  boilerplate. `Model.full_clean()` validates every field and calls
  `clean()` for model-level validation.
- **`ForeignKey` auto-relationships**: `author = fields.ForeignKey("User",
  on_delete="CASCADE", related_name="posts")` now automatically creates the
  FK constraint, the forward `relationship()` (`post.author`), and the
  reverse `relationship()` (`user.posts`) — no manual SQLAlchemy
  `relationship()`/`backref()` needed. String targets are resolved against
  the SQLAlchemy class registry with module-affinity disambiguation, and
  resolved lazily (via a `before_configured` event) so forward references
  across apps/modules work regardless of import order.
- **`ManyToManyField`**: `tags = fields.ManyToManyField("Tag",
  related_name="posts")` auto-creates a hidden join table (plain SQLAlchemy
  Core `Table`, migration-friendly) and Django-style collection helpers via
  `RelatedList` — `post.tags.add(t1, t2)`, `.remove(t)`, `.clear()`,
  `.set([...])`, `.all()`. Supports `to="self"` for self-referential M2M
  (e.g. "friends") and a `db_table=` override. Custom "through" models
  (extra columns on the join table) are not yet supported.
- **Admin system** (`fastframe.admin`): Django-like `ModelAdmin`/`admin_site`
  registry; a REST API (`GET/POST/PUT/DELETE /api/admin/{resource}`,
  `/api/admin/schema`, `/api/admin/{resource}/choices/{field}`) in React
  Admin's response envelope; a bundled React admin UI
  (`ADMIN_MODE = "static"`, the default) plus an SSR/Jinja2 fallback
  (`ADMIN_MODE = "ssr"`) and a `startadmin` scaffold for a customizable UI
  (`ADMIN_MODE = "custom"`).
- **Admin authentication** (`fastframe.admin.auth`): `POST /api/admin/login`
  / `POST /api/admin/logout` / `GET /api/admin/me`, backed by a signed,
  `httponly` session cookie (HMAC-SHA256 over `SECRET_KEY`, no extra
  dependency). All other `/api/admin/*` routes require a logged-in `User`
  with `can_access_admin = True` (`401`/`403` otherwise), gated by the new
  `ADMIN_REQUIRE_AUTH` setting (default `True`; set `False` for the old,
  unauthenticated dev-only behavior). The bundled UI and SSR views serve a
  minimal login page until a valid session exists.
- **Built-in `User` model** (`fastframe.contrib.auth`): UUID v7 (or
  `AutoField`, per `DEFAULT_AUTO_FIELD`) primary key, `username`/`email`
  (unique), PBKDF2-SHA256 password hashing (`set_password`/
  `check_password`), `is_active`, a flexible `user_data` JSON field backing
  `can_access_admin`/`is_superuser`/`permissions`/`preferences`, and
  `AUTH_USER_MODEL` for swapping in a custom user model.
  `fastframe.contrib.auth.authenticate(username, password)` and
  `get_user_model()` mirror Django's helpers of the same name.

### Changed

- `__version__` / package version bumped to `0.3.0`.

### Docs

- `docs/ADMIN_SECURITY_WARNING.md` rewritten for v0.3.0: documents the new
  authentication flow, what's still not covered (per-model/field
  permissions, CSRF, rate limiting, audit logging), and a deployment
  checklist.
- `docs/AUDIT_2026_09_23.md`, `docs/ACTION_PLAN_V0.3.md`,
  `docs/RELATIONSHIP_AUTO_GEN_COMPLETE.md`, `docs/ADMIN_COMPLETION_SUMMARY.md`
  record the audit, plan, and completion notes behind this release.

## [0.2.0] - 2026-09-22

Developer-experience release. Closes out every item under `docs/roadmap.md`'s
"v0.2 — Developer experience," and resolves nearly every long-standing
"TBD"/"(later)" placeholder left over from the pre-implementation docs.

### Added

- **Check framework**: `fastframe.core.checks.CheckMessage` / `run_checks()`, and `AppConfig.checks()` hook for apps to register their own checks. Built-in checks: empty `INSTALLED_APPS`, duplicate app labels, unimportable/typo'd app in `INSTALLED_APPS`, missing `DATABASE_URL` (always run, no I/O), plus DB connectivity and pending-migrations (opt-in via `--database`, matching Django's `check --database` precedent). `manage.py check` exits `1` on any `ERROR`/`CRITICAL` — usable as a CI gate.
- **CLI polish**:
  - `manage.py showmigrations` — lists every migration with an `[X]`/`[ ]` applied marker.
  - `manage.py dbshell` — opens the native DB client (`sqlite3`/`psql`/`mysql`) with connection args pre-filled from `DATABASE_URL`.
  - `manage.py test` now forwards flags straight through to pytest — `manage.py test -v` works without needing `manage.py test -- -v` (argparse subparsers can't reliably pass dash-prefixed tokens through `nargs=REMAINDER`; `test` is now special-cased in dispatch, `git`/`npm`-style). `--` is still accepted for backward compatibility.
  - `manage.py --version`.
  - `SettingsError` (e.g. unset `FASTFRAME_SETTINGS_MODULE`) now prints a clean one-line error and exits `1` instead of a raw traceback.
- **Lifecycle hooks**: `AppConfig.shutdown()`, run for every installed app when the ASGI app shuts down (via `get_asgi_application()`'s default `lifespan`). A caller-supplied `lifespan=` always takes precedence.
- **`.env` file support**: loaded via `python-dotenv` before the settings module is imported, without overriding real environment variables. Generated projects ship a `.env.example` (tracked) and `.gitignore` (ignoring the real `.env`, `db.sqlite3`, etc. — new; project template previously shipped none).
- **`fastframe.testing.override_settings(**kwargs)`**: context manager for temporarily overriding settings-module attributes within a single test.
- **`fastframe.http.pagination`**: `Pagination`/`pagination` — a `Depends(pagination)` FastAPI dependency parsing `?limit=&offset=`, pairing with `QuerySet.limit()`/`.offset()`. Dogfooded into `examples/todo_app`'s `GET /todos`.

### Fixed

- A typo'd `INSTALLED_APPS` entry used to fail completely silently (the app was just never used, with no error anywhere) — now caught by `manage.py check`.

### Docs

- Resolved essentially every "(TBD)"/"(later)"/"(draft)" marker in `docs/app-contract.md`, `docs/repository-layout.md`, `docs/session-lifecycle.md`, `docs/public-api-v0.1.md`, and `docs/cli.md` against what's actually shipped: settings module shape, router export convention, migration revision layout (single combined chain, documented as a deliberate decision, not an accident), app declaration order, default `AppConfig`/`apps.py` auto-creation, commit policy in requests/shell, test isolation granularity. `docs/repository-layout.md` was rewritten wholesale — it still described a pre-implementation draft ("No `src/fastframe` implementation yet") despite v0.1.0 having shipped.
- Explicitly deferred custom management command auto-discovery (`<app>/management/commands/`) to v0.6+ per `docs/roadmap.md`, rather than half-building it now.

## [0.1.0] - 2026-09-22

First tagged release. Proves the core FastFrame development loop end-to-end,
validated against a real app (`examples/todo_app`).

### Added

- Repository scaffolding: documentation, ADRs, and project metadata.
- Core package: settings loading, `INSTALLED_APPS` registry, `bootstrap()`, `get_asgi_application()`.
- CLI: global `fastframe` (`startproject`, `version`); `manage.py` commands `runserver`, `check`, `makemigrations`, `migrate`, `shell`, `test`, `startapp`.
- Database: engine from `DATABASE_URL`, request middleware, `session_scope`, `get_session` (now reuses the request's middleware-bound session instead of opening a duplicate one).
- Models: `Model` base with a thin `objects` manager backed by a lazy, chainable `QuerySet` — `all`, `filter`, `exclude`, `order_by`, `limit`, `offset`, `get`, `first`, `count`, `exists`, `create`; instance `save`, `delete`. `Model.__repr__` shows column values for shell/debugging.
- HTTP: automatic exception handlers register `DoesNotExist` → 404 and `MultipleObjectsReturned` → 500 in `get_asgi_application()`.
- Migrations: Alembic integration, per-app `migrations/versions`, `makemigrations`/`migrate`; `makemigrations` skips creating a file and prints "No changes detected." when there's nothing to autogenerate.
- Shell: stdlib REPL with model auto-import and configurable startup via `SHELL_IMPORTS`, `config/shell_startup.py`, and `AppConfig.shell()`.
- Scaffolding: `fastframe startproject` and `manage.py startapp` project templates, with automatic `INSTALLED_APPS`/router wiring.
- Project template: `tests/conftest.py` provides `project_env` and `client` fixtures out of the box (the `client` fixture builds the ASGI app *after* the database is configured, avoiding a test-isolation footgun).
- Fixtures/examples: `tests/fixtures/miniproject` (`health`, `users`, `posts` apps, including a `Post` → `User` foreign key + SQLAlchemy `relationship()` example) and `examples/todo_app`, a real end-to-end CRUD app built with the documented v0.1 loop.
- Docs: architecture, vision, design principles, MVP scope, CLI reference (including `runserver`'s `[addrport]` syntax and `manage.py test -- <pytest args>` forwarding), session lifecycle, shell, public API draft, roadmap, non-goals, repository layout, development guide.
- CI workflow (ruff + pytest on Python 3.11/3.12).
- ADR 0006: sync SQLAlchemy for v0.1.

### Fixed

- CLI: `runserver <port>` (a bare port number with no host, e.g. `runserver 8123`) was incorrectly treated as a hostname with the default port, causing bind failures. Now binds to the default host on that port, matching Django's `runserver` convention.

### Changed

- README and project URLs point to `0xdps/fast-frame`.
