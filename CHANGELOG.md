# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Shell: configurable startup via `SHELL_IMPORTS`, `config/shell_startup.py`, and `AppConfig.shell()` (stdlib REPL only).
- Documentation: [docs/shell.md](docs/shell.md).

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
