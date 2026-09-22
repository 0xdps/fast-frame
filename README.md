# FastFrame

**A batteries-included Python web framework built on FastAPI.**

FastFrame aims to provide a **Django-like developer experience** from initial development through production, while using **FastAPI** as its HTTP/ASGI foundation. The goal is not to recreate Django feature-for-feature. Instead, FastFrame offers strong conventions, sensible defaults, and a cohesive workflow by composing mature Python libraries underneath.

> **Django's developer experience, FastAPI's foundation, and modularity by default.**

## Status

**v0.2 released.** v0.1's core development loop — `fastframe startproject`, `manage.py` (`runserver`, `migrate`, `shell`, `test`, `startapp`), thin models with a chainable `QuerySet`, and Alembic migrations — is implemented and validated end-to-end against a real app (see [`examples/todo_app`](examples/todo_app)). v0.2 adds developer-experience polish on top: a real `check`/`check --database` framework, `showmigrations`/`dbshell`, app lifecycle hooks (`AppConfig.checks()`/`shutdown()`), `.env` support, a pagination dependency, and test utilities (`fastframe.testing.override_settings`). See [docs/development.md](docs/development.md), [docs/mvp-v0.1.md](docs/mvp-v0.1.md), and [docs/roadmap.md](docs/roadmap.md).

## What FastFrame is (and is not)

| FastFrame provides | FastFrame does not (initially) |
| --- | --- |
| `manage.py`-style project workflow | Django-style views or URL dispatch |
| Apps, settings, and extension hooks | A full QuerySet / ORM algebra |
| Thin model helpers (`filter`, `get`, `save`, …) | Hiding SQLAlchemy for complex queries |
| Migrations (Alembic, convention-driven) | Admin, auth, templates, static files (later) |
| Shell, runserver, test integration | Replacing FastAPI routing or Pydantic |

HTTP stays **FastAPI**. Hard data access stays **SQLAlchemy**. FastFrame owns **lifecycle, conventions, and the daily loop**.

## Developer loop

```text
fastframe startproject myproject
cd myproject
python manage.py runserver

python manage.py startapp users
# define models in users/models.py
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py shell
python manage.py dbshell
python manage.py test -v
python manage.py check --database
```

Inside a generated project, `manage.py` is the familiar entry point (similar to Django). The global installer CLI is `fastframe` (see [docs/cli.md](docs/cli.md)).

## Documentation

| Document | Description |
| --- | --- |
| [Vision & thesis](docs/vision-and-thesis.md) | Product direction and positioning |
| [Design principles](docs/design-principles.md) | How we make tradeoffs |
| [Architecture](docs/architecture.md) | Components and dependencies |
| [MVP v0.1](docs/mvp-v0.1.md) | First release scope and success criteria |
| [Roadmap](docs/roadmap.md) | v0.2+ direction |
| [Non-goals](docs/non-goals.md) | What we explicitly drop or defer |
| [App contract](docs/app-contract.md) | Installed apps and extension points |
| [Session lifecycle](docs/session-lifecycle.md) | DB session rules |
| [Public API](docs/public-api-v0.1.md) | Stable surface (v0.1 + v0.2) |
| [Shell](docs/shell.md) | Stdlib REPL, `SHELL_IMPORTS`, startup script |
| [Repository layout](docs/repository-layout.md) | This repo and future package structure |
| [Contributing](CONTRIBUTING.md) | How to participate |

Architecture decisions are recorded in [adr/](adr/).

## Technology direction (implementation choices)

| Layer | Planned technology |
| --- | --- |
| HTTP / ASGI | FastAPI |
| Server (dev) | Uvicorn |
| Validation | Pydantic |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| CLI | Python management commands |

These are implementation choices, not necessarily permanent public API commitments. FastFrame's abstraction should remain stable even if an underlying dependency changes.

## License

MIT — see [LICENSE](LICENSE).

## Links

- Repository: [github.com/0xdps/fast-frame](https://github.com/0xdps/fast-frame)
- PyPI package name (planned): **fastframe**
