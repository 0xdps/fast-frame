# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
