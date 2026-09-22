# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Shell: configurable startup via `SHELL_IMPORTS`, `config/shell_startup.py`, and `AppConfig.shell()` (stdlib REPL only).
- Documentation: [docs/shell.md](docs/shell.md).
- Models: `QuerySet` with chainable `order_by`, `limit`, `offset`, `exclude`, `exists`; `Manager` methods now return `QuerySet` (lazy, list-like, backward compatible).
- HTTP: automatic exception handlers register `DoesNotExist` → 404 and `MultipleObjectsReturned` → 500 in `get_asgi_application()`.
- Models: `Model.__repr__` shows column values for shell/debugging ergonomics.
- Migrations: `makemigrations` now skips creating a migration file and prints "No changes detected." when autogenerate finds no schema changes.
- Example: `examples/todo_app`, a real end-to-end app (FK-free CRUD) built with the documented v0.1 loop, used to dogfood the framework — see its README for what it validated.
- Fixture: `posts` app with a `Post` → `User` foreign key and SQLAlchemy `relationship()` example (manager + escape-hatch usage).
- Docs: [docs/cli.md](docs/cli.md) documents `runserver`'s Django-style `[addrport]` argument and the `manage.py test -- <pytest args>` forwarding syntax.
- Project template: `tests/conftest.py` now also provides a `client` fixture (`TestClient` built from `config.asgi.application` *inside* the fixture, after `project_env` configures the database) to prevent a footgun where importing `application` at module level leaks state between tests.

### Fixed

- CLI: `runserver <port>` (a bare port number with no host, e.g. `runserver 8123`) was incorrectly treated as a **hostname** with the default port, causing bind failures. It now binds to the default host on that port, matching Django's `runserver` convention.
- DB: `get_session()` FastAPI dependency now reuses the request's existing middleware-bound session instead of opening a duplicate one; still opens its own session for standalone (non-middleware) use.

### Changed

- README and project URLs point to `0xdps/fast-frame`.

### Added (initial release)

- Repository scaffolding: documentation, ADRs, and project metadata.
- Core package: settings loading, `INSTALLED_APPS` registry, `bootstrap()`, `get_asgi_application()`.
- CLI: global `fastframe` (version stub), `manage.py` commands `runserver` and `check`.
- Integration fixture `tests/fixtures/miniproject` with `/health` endpoint.
- CI workflow (ruff + pytest on Python 3.11/3.12).
- ADR 0006: sync SQLAlchemy for v0.1.
- Database: engine from `DATABASE_URL`, request middleware, `session_scope`, `get_session`.
- Models: `Model` base with thin `objects` manager (`filter`, `get`, `create`, `count`, `save`, `delete`).
- Miniproject `users` app with `GET /users/{id}`.
- Migrations: Alembic integration, `makemigrations` / `migrate`, per-app `migrations/versions`.
- Committed initial migration for miniproject `User` model.
- CLI: `shell`, `test` (pytest), `startapp`, and `fastframe startproject` with project templates.
