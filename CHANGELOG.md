# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

`0.1.0` is the first release. Commit messages that say `v0.2.0`,
`v0.3.0`, or `v0.4.0` are pre-release working names, not package
versions. After this release: fixes bump the patch version, a new
feature bumps the minor version.

## [Unreleased]

### Changed

- Background jobs are the next battery ([ADR 0012](docs/adr/0012-background-jobs.md)):
  an optional `fastframe.tasks` app on Celery. Redis is the documented
  broker. `manage.py work` starts a worker and `manage.py beat` starts
  the scheduler. Email and object storage are out of scope, including
  `FileField` / `ImageField`. Templates, caching, signals, and app
  management commands stay planned and are not part of the jobs app.
- The admin has no Jinja UI, and Phase 5 will not add one. Templates in
  that phase are for app views. ADR 0007 no longer lists the admin as the
  first Jinja consumer.
- Docs describe the 0.1.3 tree. ADR 0007 and ADR 0008 keep their original
  decisions and add a note on later moves: SSR was dropped, then the
  bundled admin left React Admin for the Tailwind UI.
- `ADMIN_SITE_TITLE` and `ADMIN_SITE_HEADER` set the admin sidebar, browser
  tab, and sign-in heading. The UI reads them from `GET /api/admin/schema`.
- A record opens read-only, with the same fields disabled. Edit turns
  them on, and Save returns to the read-only page.
- Choice and foreign-key fields use an in-app menu, and scrollbars use
  the admin's own thumb instead of the browser default. Foreign-key
  search lives inside that menu.
- The record page link back to the list is a static Back control, and the
  primary key is the first field on every model.
- Foreign keys show the related object's name in the list and on the record,
  and that name links to the related record.

### Added

- A pre-commit hook formats Python with Ruff and lints with Ruff and
  Pylint. Enable it with `pre-commit install` after
  `pip install -e ".[dev]"`.

## [0.1.3] - 2026-10-02

### Added

- Admin dashboard redesign: the model-tile grid is gone, replaced by a
  "Recent activity" panel sourced from `AuditLog` (skipped entirely if
  the current user can't view it). The sidebar now has a search box that
  filters models by name, models are grouped under their own app with
  each app section collapsible (state persists locally), and the top
  bar has a user menu (avatar, "My profile", a dark-mode toggle, "Log
  out") backed by `/me` and `/logout`. A matching dark theme was added
  alongside the existing light one.

### Changed

- Admin sidebar no longer collapses. The collapse control is gone, and
  the FastFrame header at the top of the sidebar opens the dashboard.
- The top bar no longer repeats the page title. Overview and model names
  stay in the main content.
- Admin UI is now built with Tailwind and shadcn-style components. It no
  longer depends on react-admin or Material UI. Lists, forms, the sidebar,
  the overview, and the user menu still come from the admin schema and the
  same `/api/admin` endpoints.
- Admin: the Audit Log is no longer a sidebar entry. The dashboard's
  Recent activity panel shows a short preview (who, what, when) and is
  the only place that links to the full audit history.
- Admin: collapsing the sidebar no longer lets the "FastFrame" wordmark
  spill out of the 64px rail. The closed state shows only the mark,
  centered, and menu icons are centered in the rail as well.
- Migrations: `makemigrations` writes each app's changes into that app's
  `migrations` directory. A change to one app is no longer appended to
  whichever installed app happens to be first. Framework apps such as
  `fastframe.contrib.auth` go to `config/migrations` instead, since they
  are not a directory in the project. `showmigrations` groups files by
  the app that owns them.

### Fixed

- Admin user search (`GET /api/admin/user?q=`) no longer crashes. The
  built-in user admin was combining querysets with `|`, which querysets
  do not support, so any search term raised `TypeError` (reported by
  Starlette as an `ExceptionGroup`). Search now uses the shared
  `search_fields` path.
- `GET /counts` (`/api/admin/counts` and `/api/v1/counts`) now applies the
  same authorization as `/{resource}`: a model the caller lacks
  `get_has_view_permission` for is omitted from the response instead of
  having its row count included regardless. A model with a custom, row-
  filtering `get_queryset()` override is now counted through that
  queryset rather than a raw `COUNT(*)` on the full table, so its total
  matches what `/{resource}` actually lists. Models using the default,
  unfiltered queryset are still counted together in a single combined
  query — only models with a genuine override cost an extra query each.
- `GET /schema` no longer opens an unused database session — it depended
  on one but never used it, contradicting its own "no database queries"
  docstring and adding needless per-request DB overhead.
- Admin dark mode: the new "Recent activity" panel, user profile header,
  password-change panel, and user edit/create form were hand-styled with
  hardcoded light colors, so toggling dark mode left them stuck white
  against an otherwise-dark page. The Save/Delete toolbar on edit/create
  forms had the same problem for a different reason — react-admin's own
  default theme (spread as a base into both our light and dark themes)
  hardcodes that toolbar's background regardless of mode. All of the
  above now track the active theme (`theme.ts`'s `RaToolbar` override for
  the toolbar; new CSS variables in `index.css`, kept in sync with the
  resolved theme mode via a `data-theme` attribute set in `userMenu.tsx`,
  for everything else).
- Admin sidebar: the model list didn't actually scroll on its own (a
  missing `min-height: 0` on a flex item let it grow past the sidebar's
  height instead of shrinking to fit), so once its content overflowed,
  the whole sidebar — including the brand and search box — scrolled as
  one unit instead of staying pinned while only the list scrolled.
  Scrollbars app-wide (sidebar included) are now also slim and
  theme-colored instead of the browser/OS default.
- Admin sidebar: the visible fixed sidebar (`.RaSidebar-fixed`) had no
  explicit width, so it shrank to fit its content instead of matching its
  own reserved-space spacer (`.RaSidebar-docked`, sized to
  `theme.sidebar.width`/`closedWidth`). That left a sliver on the right
  edge uncovered by the fixed layer; it only *looked* fine at rest because
  the (non-fixed) spacer happened to paint the same background there —
  but that spacer scrolls away with the page while the fixed sidebar
  doesn't, so the gap would open up and grow as soon as you scrolled.
  `.RaSidebar-fixed` now has an explicit width matching the spacer in
  both the open and collapsed states.
- Admin sidebar: model-link icons flipped between near-black and white
  depending on the light/dark toggle, while their labels stayed a fixed
  color — because the icon is wrapped in MUI's `ListItemIcon`, which sets
  its own theme-dependent default color independently of whatever color
  we set on the link. The sidebar keeps a permanently dark background
  regardless of theme, so its icons now stay fixed too, same as the text.
- Admin: on a short window, scrolling the main content or the sidebar's
  menu list past its top/bottom edge triggered the browser's native
  rubber-band bounce, briefly revealing empty space beyond the actual
  content (and letting the scroll "chain" into the page behind it).
  Fixed by turning the admin into a proper fixed "app shell": `html`/
  `body`/`#root` are now pinned to exactly the viewport height with
  `overflow: hidden` (the page itself never scrolls), and react-admin's
  main content area (`.RaLayout-content`) is made its own bounded,
  independently-scrollable box instead — the same pattern the sidebar's
  menu list already used. `overscroll-behavior: none` on just those two
  real scroll containers (main content, sidebar list) then disables the
  bounce without breaking scroll *chaining* elsewhere — an earlier,
  broader attempt at this fix applied it to every element via a `*`
  selector, which also blocks chaining, and ended up making forms
  unscrollable whenever a nested MUI wrapper had any scrollable region
  of its own between the content and the page.

## [0.1.2] - 2026-09-27

### Changed

- The health check is now a built-in, opt-in app (`fastframe.health`)
  instead of a boilerplate `health/` app folder in every generated
  project. Add `"fastframe.health"` to `INSTALLED_APPS` to mount
  `GET /health`; freshly generated projects include it by default.
- The health check is overridable: `HEALTH_PATH` changes the route
  (default `/health`) and `HEALTH_CHECK` (a dotted path or callable
  returning a JSON-serializable body) replaces the default
  `{"status": "ok"}` response.

## [0.1.1] - 2026-09-27

### Fixed

- `fastframe startproject` no longer crashes with a `UnicodeDecodeError`
  when the installed package contains compiled `__pycache__/*.pyc` files
  inside the project template (scaffolding now skips bytecode artifacts).
- Fixed the test suite running under pytest 9: the repo root is now added
  to `pythonpath` so `import tests.fixtures.*` and
  `FASTFRAME_SETTINGS_MODULE = "tests.fixtures.*"` resolve correctly.
- Disabled the false-positive Pylint `E1137`
  (`unsupported-assignment-operation`) error on field descriptors (e.g.
  `JSONField`) that return mutable containers at runtime.

## [0.1.0] - 2026-09-27

First release. The distribution name is `fast-frame`. Two threads that
were drafted as an unreleased `0.2.0` are part of this release, not a
later version:
batteries mount through `INSTALLED_APPS`, and the ORM covers day-to-day
CRUD without becoming a second query algebra.

### Added

**App registry for batteries — `INSTALLED_APPS` replaces `ENABLE_*`**

- `AppConfig.get_routers()`: a new, optional hook returning routers built
  at mount time (e.g. from settings), collected by
  `AppsRegistry.get_routers()` in `INSTALLED_APPS` order and mounted by
  `get_asgi_application()` alongside the existing `urls.py` → `router`
  convention. `AppsRegistry.is_installed(name)` for checking membership
  directly. See [docs/app-contract.md](docs/app-contract.md#router-discovery).
- `fastframe.admin`, `fastframe.contrib.auth`, and `fastframe.api` each
  ship an `AppConfig` (`AdminConfig`, `AuthConfig`, `RestApiConfig`) and
  are now mounted purely by being listed in `INSTALLED_APPS` — the same
  as any other app. Nothing about admin/auth/the REST API is imported or
  routed unless the corresponding entry is present.
- `get_asgi_application()` is now the single, canonical application
  factory: it applies `MIDDLEWARE`/CORS/security headers and mounts
  every installed app's routers (in addition to what it already did —
  `ROOT_URLCONF` routers, DB session middleware, exception handlers).
  `create_app()` is now a thin, **deprecated** alias for it.
- A freshly generated project (`fastframe startproject`) does not
  install admin, general auth, or the REST API by default.

**Richer ORM — still a thin layer over SQLAlchemy, not a second query
algebra ([docs/orm-features.md](docs/orm-features.md))**

- `F()` field-reference expressions are wired up end-to-end (previously
  present as a class but non-functional): `.filter(karma__gt=F("num_posts"))`
  compares two columns in SQL; `obj.field = F("field") + 1; obj.save()`
  issues a single atomic `UPDATE ... SET field = field + 1`, safe under
  concurrent writers. `+`, `-`, `*`, `/` supported, mixable with plain
  numbers. `Q()` objects and Django-style field lookups (`__gte`,
  `__icontains`, `__in`, `__isnull`, …) already worked and are now
  documented.
- `select_related()` / `prefetch_related()`: eager loading for
  ForeignKey/reverse-FK/many-to-many relationships (`joinedload`/
  `selectinload` under the hood), the direct answer to the classic N+1
  query trap. Supports Django-style `__` nesting
  (`select_related("author__profile")`).
- `bulk_create(objects, batch_size=None)` / `bulk_update(objects, fields,
  batch_size=None)` on the manager; `QuerySet.update(**kwargs)` /
  `.delete()` for single-statement bulk writes over every row matching
  the current filter, without loading objects into Python.
- `get_or_create(defaults=None, **kwargs)` / `update_or_create(defaults=None,
  **kwargs)`, Django-style, returning `(instance, created)`.
- `values(*fields)` / `values_list(*fields, flat=False)`: dict/tuple/
  scalar projections that skip full model instantiation.
- `only(*fields)` / `defer(*fields)`: partial column loading (`load_only`/
  `defer`) while still returning full model instances.
- `atomic()` (`fastframe.db` and `fastframe.models`): a context manager
  wrapping a SAVEPOINT around the current session; nestable, rolls back
  only its own block on error.

### Fixed

- Migrations: per-app migration directory discovery now skips dotted,
  framework-provided app names (e.g. `fastframe.contrib.auth`) instead of
  attempting to create a literal, invalid directory named that at the
  project root.
- `bulk_update()` and the F-expression save path both guard against
  SQLAlchemy autoflush firing before their explicit statement runs
  (`session.no_autoflush` / `session.expire()`), which could otherwise
  silently persist unrelated in-memory changes or choke on an
  unresolved `F()` placeholder.

### Removed

- `ENABLE_ADMIN`, `ENABLE_AUTH_API`, `ENABLE_REST_API` settings — replaced
  entirely by `INSTALLED_APPS` membership. `create_app(include_admin=...)`'s
  unused kwarg is also gone (it had zero real usages).

The rest of this candidate is the core loop, admin, REST API, and auth
work below. It was drafted under pre-release labels (`v0.2` / `v0.3` /
`v0.4` in commit messages). Those labels are not releases.

### Also in this candidate

**API**

- `FastFrameAPI` (`from fastframe.http import FastFrameAPI`). Function routes
  (`@api.get("/users")`) and resource routes (`@api.route("/users")` on a
  class whose methods are HTTP verbs). The path is always explicit. A
  class name is never a URL. Returned `Model` and `QuerySet` values
  serialize to field dicts. Pydantic, `response_model`, and `Depends`
  stay FastAPI's. `api.include_router` mounts a native `APIRouter`.
  An installed app may export `api` from `<app>.api`; that router is
  mounted beside the app's `urls.py` router. A missing `api.py` is fine.
  See ADR 0009.
- Swagger, ReDoc, and `/openapi.json` are now the `fastframe.docs` app.
  Add `"fastframe.docs"` to `INSTALLED_APPS` to mount them. A project
  that does not list it has no docs routes. `ENABLE_OPENAPI`,
  `OPENAPI_URL`, `SWAGGER_UI_URL`, `REDOC_URL`, `OPENAPI_TITLE`,
  `OPENAPI_VERSION`, and `OPENAPI_DESCRIPTION` are removed. The schema
  title is `APP_NAME`.
- `BaseModel` and `Field` are re-exported from Pydantic
  (`from fastframe.schemas import BaseModel, Field`). They are the Pydantic
  objects, not a subclass. See ADR 0010.

**Records (no behavior change)**

- Roadmap Phase 3 no longer tells readers to opt into the REST API with
  `ENABLE_REST_API`. That setting does not exist. The switch is
  `"fastframe.api"` in `INSTALLED_APPS`.
- ADR 0003 lists the ORM surface in this candidate, and the methods that
  still require a superseding ADR (`annotate()`, subquery composition,
  window functions, `ManyToManyField(through=...)`, a FastFrame
  `select()`).
- ADR 0007 no longer points at a later admin SPA package. That note used
  a pre-release version label. The decision remains: admin is React-only
  (ADR 0008).
- Non-goals no longer send eager loading to SQLAlchemy. Declared-relation
  `select_related()` / `prefetch_related()` are in the thin layer.
  Locking, window functions, and `annotate()` are not.
- `test_admin_not_mounted_unless_installed` no longer documents the
  removed `ENABLE_ADMIN` setting. Behavior was already `INSTALLED_APPS`.

**Core loop**

- Settings loading, `INSTALLED_APPS` registry, `bootstrap()`,
  `get_asgi_application()` / `create_app()`.
- CLI: global `fastframe` (`startproject`, `version`); `manage.py`
  commands `runserver`, `check` (`--database` for connectivity/pending-
  migrations checks), `makemigrations`, `migrate`, `showmigrations`,
  `dbshell`, `shell`, `test` (forwards flags straight through to pytest),
  `startapp`, `startadmin`, `createadminuser`, `--version`.
- `AppConfig.checks()` and `AppConfig.shutdown()` lifecycle hooks;
  `fastframe.core.checks.CheckMessage`/`run_checks()` (built-in checks:
  empty `INSTALLED_APPS`, duplicate app labels, unimportable apps, missing
  `DATABASE_URL`); `manage.py check` exits `1` on any `ERROR`/`CRITICAL` —
  usable as a CI gate. A typo'd `INSTALLED_APPS` entry, previously silent,
  is now caught here.
- `.env` file support via `python-dotenv`, loaded before the settings
  module is imported, without overriding real environment variables.
- `SettingsError` (e.g. unset `FASTFRAME_SETTINGS_MODULE`) prints a clean
  one-line error and exits `1` instead of a raw traceback.
- Database: engine from `DATABASE_URL`, request middleware,
  `session_scope`, `get_session`.
- Migrations: Alembic integration, per-app `migrations/versions`,
  `makemigrations`/`migrate`.
- Shell: stdlib REPL with model auto-import and configurable startup
  (`SHELL_IMPORTS`, `config/shell_startup.py`, `AppConfig.shell()`).
- HTTP: automatic exception handlers register `DoesNotExist` → 404 and
  `MultipleObjectsReturned` → 500.
- `fastframe.http.pagination`: a `Depends(pagination)` FastAPI dependency
  parsing `?limit=&offset=`, pairing with `QuerySet.limit()`/`.offset()`.
- `fastframe.testing.override_settings(**kwargs)`: context manager for
  temporarily overriding settings-module attributes within a single test.

**Models and fields**

- `Model` base with a thin `objects` manager backed by a lazy, chainable
  `QuerySet` — `all`, `filter`, `exclude`, `order_by`, `limit`, `offset`,
  `get`, `first`, `count`, `exists`, `create`; instance `save`, `delete`.
- Declarative fields (`fastframe.models.fields`): `CharField`, `TextField`,
  `IntegerField`, `BigIntegerField`, `SmallIntegerField`, `BooleanField`,
  `FloatField`, `DateField`, `DateTimeField` (`auto_now`/`auto_now_add`),
  `DecimalField`, `EmailField`, `URLField`, `UUIDField` (UUID v7 by
  default), `JSONField`, `AutoField`/`BigAutoField`, replacing raw
  `mapped_column()` boilerplate. `Model.full_clean()` validates every
  field and calls `clean()` for model-level validation.
- `ForeignKey` auto-relationships: `author = fields.ForeignKey("User",
  on_delete="CASCADE", related_name="posts")` creates the FK constraint
  and both the forward (`post.author`) and reverse (`user.posts`)
  `relationship()` automatically. String targets resolve against the
  SQLAlchemy class registry (module-affinity disambiguation), lazily (via
  a `before_configured` event) so forward references across
  apps/modules work regardless of import order.
- `ManyToManyField`: `tags = fields.ManyToManyField("Tag",
  related_name="posts")` auto-creates a hidden join table and
  Django-style collection helpers via `RelatedList` — `.add()`,
  `.remove()`, `.clear()`, `.set([...])`, `.all()`. Supports `to="self"`
  for self-referential M2M and a `db_table=` override. Custom "through"
  models (extra columns on the join table) are not yet supported.
- `DEFAULT_AUTO_FIELD` (`AutoField` / `BigAutoField` / `UUIDField`)
  chooses the primary-key column type for models that don't declare one.

**Admin**

- Django-like `ModelAdmin`/`admin_site` registry; a REST API
  (`GET/POST/PUT/DELETE /api/admin/{resource}`, `/api/admin/schema`,
  `/api/admin/{resource}/choices/{field}`) in React Admin's response
  envelope; a bundled React admin UI (`ADMIN_MODE = "static"`, the
  default, or `"custom"` for a project-built UI via `manage.py
  startadmin`). The admin is React-only.
- Session authentication, always required: `POST /api/admin/login` /
  `POST /api/admin/logout` / `GET /api/admin/me`, backed by a signed,
  `httponly` session cookie (HMAC-SHA256 over `SECRET_KEY`). Every other
  `/api/admin/*` route requires a logged-in `User` with
  `can_access_admin = True` (`401`/`403` otherwise). The bundled UI serves
  a minimal login page until a valid session exists.
- Audit log (`fastframe.admin.audit.AuditLog`): every create, update, and
  delete made through the admin API or the REST API is recorded — who,
  what (model, object id/repr), when, which surface (`source`:
  `"admin"`/`"api"`), and the changed values (full snapshot for
  create/delete, changed-fields-only diff for update). Read-only,
  browsable in the admin UI like any other model.

**Generic REST API**

- `fastframe.api`, opt-in by listing it in `INSTALLED_APPS`: token-authenticated CRUD
  (`GET/POST/PUT/DELETE /api/v1/{resource}`, `/api/v1/schema`,
  `/api/v1/{resource}/choices/{field}`) over the same models registered
  with `admin_site`, for non-browser clients that can't carry a session
  cookie. `POST /api/auth/token` exchanges username/password for an
  opaque bearer token (`secrets.token_hex(32)`, stored only as its
  SHA-256 hash, shown once); `DELETE /api/auth/token` revokes it. Any
  active user (not just `can_access_admin`) may authenticate. Internally,
  the admin API and this API share one CRUD implementation
  (`fastframe.admin.api._build_crud_router`), parameterized by which auth
  dependency guards it.
- Token expiry: `Token.expires_at` (nullable), `API_TOKEN_DEFAULT_EXPIRY_DAYS`
  setting, and an optional `expires_in_days`/`expiresInDays` argument to
  `create_token()`/`POST /api/auth/token`. An expired token is rejected
  exactly like a revoked one.

**Auth and permissions**

- Built-in `User` model (`fastframe.contrib.auth`): UUID v7 (or
  `AutoField`, per `DEFAULT_AUTO_FIELD`) primary key, `username`/`email`
  (unique), PBKDF2-SHA256 password hashing (`set_password`/
  `check_password`, compared with `hmac.compare_digest`), `is_active`, a
  flexible `user_data` JSON field backing `can_access_admin`/
  `is_superuser`/`permissions`/`preferences`, and `AUTH_USER_MODEL` for
  swapping in a custom user model. `authenticate(username, password)` and
  `get_user_model()` mirror Django's helpers of the same name, and always
  perform a full password-hash comparison (against a dummy hash for
  unknown/inactive usernames) to avoid a timing side-channel that would
  otherwise leak which usernames exist.
- Password strength validation (`fastframe.contrib.auth.validators`):
  `User.set_password()` validates length (`PASSWORD_MIN_LENGTH`, default
  `8`) and rejects a password equal to the username, before hashing.
  `validate=False` is available as an escape hatch.
- Permissions (`fastframe.contrib.auth.permissions`, new `Group` model):
  Django-style permission strings (`"blog.change_post"`) on
  `User.permissions` and `Group.permissions`, with `User.groups`
  (many-to-many). `ModelAdmin.enforce_permissions` (default `False`, fully
  backward compatible) opts a model in to per-request `has_*_permission`
  checks resolved against the current user's effective permissions;
  superusers always pass, and an explicit `has_*_permission = False`
  remains a hard override even for matching permissions. New
  `get_has_view_permission`/`get_has_add_permission`/
  `get_has_change_permission`/`get_has_delete_permission(user)` methods on
  `ModelAdmin` back every admin API and REST API route. See
  [docs/permissions.md](docs/permissions.md).
- `readonly_fields`/`fields`/`exclude` are enforced on write: these filter
  create/update payloads (`ModelAdmin.get_editable_fields`) — a client
  can't set a field marked read-only just by including it in the request
  body. The schema marks these fields `"readOnly": true`.
- General-purpose session auth outside `/admin`
  (`fastframe.contrib.auth.views`, `fastframe.contrib.auth.dependencies`):
  `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
  (present when `fastframe.contrib.auth` is in `INSTALLED_APPS`), independent of
  `can_access_admin` and sharing the same signed session cookie as the
  admin. New FastAPI dependencies for any app router: `get_current_user`,
  `login_required`, `permission_required(perm)`. See
  [docs/auth.md](docs/auth.md#general-purpose-session-auth-outside-admin).
- Session revocation: `User.session_version` (embedded in the signed
  session cookie payload) plus `User.invalidate_sessions()` — bumping it
  invalidates every previously issued cookie for that user immediately,
  without a session table.
- Rate limiting (`fastframe.core.ratelimit`): in-memory sliding-window
  limiter with lockout, applied to `/api/admin/login`, `/api/auth/login`,
  and `/api/auth/token` (`RATE_LIMIT_LOGIN_*` settings; `429` +
  `Retry-After` when locked out). Single-process only by design.
- CORS + security headers + a working `MIDDLEWARE` setting
  (`fastframe.middleware.security.SecurityHeadersMiddleware`,
  `fastframe.core.app._apply_middleware`): `MIDDLEWARE` (dotted paths) is
  applied by `get_asgi_application()`. `SECURE_HEADERS` (default `True`) adds
  `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` always,
  and `Strict-Transport-Security` when `DEBUG = False`.
  `CORS_ALLOWED_ORIGINS` (default `[]`, disabled) opts in to Starlette's
  `CORSMiddleware`.

**Scaffolding, fixtures, and docs**

- `fastframe startproject` and `manage.py startapp` project templates,
  with automatic `INSTALLED_APPS`/router wiring; `tests/conftest.py`
  ships `project_env` and `client` fixtures out of the box.
- `tests/fixtures/miniproject` (`health`, `users`, `posts` apps, including
  a `Post` → `User` foreign key example) and `examples/todo_app`, a real
  end-to-end CRUD app.
- Docs: architecture, vision, design principles, roadmap, non-goals,
  repository layout, development guide, CLI reference, session lifecycle,
  shell, public API surface, settings reference, auth, permissions,
  models/fields design, admin setup/customization/deployment, REST API,
  and [docs/ADMIN_SECURITY_WARNING.md](docs/ADMIN_SECURITY_WARNING.md)
  (current security posture and deployment checklist).
- CI workflow (ruff + pytest on Python 3.11/3.12). ADR 0006 (sync
  SQLAlchemy), ADR 0007/0008 (React-only admin, superseding an earlier
  SSR/Jinja2 attempt that was tried and then removed entirely, along with
  the `jinja2` dependency).

### Fixed

- CLI: `runserver <port>` (a bare port number with no host, e.g.
  `runserver 8123`) was incorrectly treated as a hostname with the
  default port, causing bind failures. Now binds to the default host on
  that port, matching Django's `runserver` convention.
- `list_records` and `fk_choices` in the admin/REST API previously
  performed **no** permission check at all, regardless of
  `has_view_permission`. Both now enforce it like every other route.
- A stale, duplicate `_snapshot_user` in `fastframe.api.auth` didn't
  include `permissions`/`is_superuser`, so every permission check on the
  REST API surface silently evaluated against an empty permission set.
  Replaced with the shared `snapshot_user` from
  `fastframe.contrib.auth.dependencies`.
- Three framework bugs uncovered while adding the first genuine
  forward-referenced many-to-many relationship (`User.groups` → `Group`,
  defined later in the same module) — none specific to any one feature,
  but all silently masked until this point:
  - `models/base.py`: the SQLAlchemy `before_configured` event listener
    that resolves deferred forward-referenced FK/M2M targets was
    registered on `Model` (a mapped class) instead of `Mapper` (the
    actual required global-event target) — it never fired. Every prior
    FK/M2M test happened to define its target class before the
    referencing class, so eager resolution always succeeded and this dead
    code path went unexercised.
  - `core/bootstrap.py`: `bootstrap()` now calls
    `sqlalchemy.orm.configure_mappers()` after all apps' `.ready()` hooks
    run, so deferred relationships are resolved — and their join tables
    registered in `Model.metadata` — before any caller's subsequent
    `Model.metadata.create_all()`.
  - `models/fields.py`: `JSONField` now wraps its SQLAlchemy type in
    `sqlalchemy.ext.mutable.MutableDict`/`MutableList` when its `default`
    is `dict`/`list`. Without this, in-place mutations
    (`user.user_data["key"] = value`) were invisible to SQLAlchemy's
    dirty-tracking and silently failed to persist on `UPDATE` (the
    initial `INSERT` was unaffected).
