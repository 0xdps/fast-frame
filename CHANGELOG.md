# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
