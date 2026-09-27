# FastFrame

<p align="center">
  <img src="brand/logo.png" alt="FastFrame" width="96" height="96">
</p>

**A batteries-included Python web framework built on FastAPI.**

FastFrame aims to provide a **Django-like developer experience** from initial development through production, while using **FastAPI** as its HTTP/ASGI foundation. The goal is not to recreate Django feature-for-feature. Instead, FastFrame offers strong conventions, sensible defaults, and a cohesive workflow by composing mature Python libraries underneath.

> **Django's developer experience, FastAPI's foundation, and modularity by default.**

## Status

**v0.1.2.** `v0.1.0` and `v0.1.1` were tagged but their wheels did not build. This tree is
still under test. The core development loop — `fastframe startproject`,
`manage.py` (`runserver`, `migrate`, `shell`, `test`, `startapp`), thin
models with a chainable `QuerySet`, and Alembic migrations — is
implemented and validated end-to-end against a real app (see
[`examples/todo_app`](examples/todo_app)), alongside developer-experience
tooling (`check`/`check --database`, `showmigrations`, `dbshell`, app
lifecycle hooks, `.env` support, test utilities).

On top of that: a Django-style admin (declarative `fields.*` with
automatic `ForeignKey`/`ManyToManyField` relationship generation, a REST
admin API, and a bundled React admin UI); a generic, token-authenticated
REST API over the same registered models; an audit log; and a built-in
`User` model with **session-based login/logout** (`can_access_admin`-gated
for the admin by default), **opt-in per-model permissions** (`Group`,
permission strings — see [docs/permissions.md](docs/permissions.md)),
**general-purpose session auth for non-admin routes**, rate limiting on
login/token endpoints, session revocation, and CORS/security headers.
Admin, general auth, the token REST API, and Swagger
(`fastframe.docs`) are **batteries you opt into via `INSTALLED_APPS`**.
A freshly generated project installs none of them. Your own endpoints
live in `<app>.api` as a `FastFrameAPI`, imported from `fastframe.http`.
Request models are `BaseModel` and `Field` from `fastframe.schemas`
(Pydantic, re-exported, not wrapped). A native `APIRouter` in `urls.py`
still works. See [docs/api-layer.md](docs/api-layer.md) and
[docs/app-contract.md](docs/app-contract.md). Current
security posture and open gaps (CSRF, per-object permissions): see
[docs/ADMIN_SECURITY_WARNING.md](docs/ADMIN_SECURITY_WARNING.md).

The ORM stays a thin layer over SQLAlchemy, but covers the day-to-day 90%
of CRUD workflows: `Q()`/`F()` and Django-style field lookups,
`select_related()`/`prefetch_related()` eager loading, bulk
create/update/delete, `get_or_create()`/`update_or_create()`,
`values()`/`values_list()`, `only()`/`defer()`, and an `atomic()`
transaction helper — see [docs/orm-features.md](docs/orm-features.md).

See [docs/development.md](docs/development.md), [docs/mvp-v0.1.md](docs/mvp-v0.1.md),
and [docs/roadmap.md](docs/roadmap.md) for what's next (templates/static
files, then additional batteries).

## What FastFrame is (and is not)

| FastFrame provides | FastFrame does not (initially) |
| --- | --- |
| `manage.py`-style project workflow | Django-style views or URL dispatch |
| Apps, settings, and extension hooks | A full query-algebra ORM (no `annotate()`, no subquery/window functions) |
| Rich-enough model helpers: `filter`/`Q`/`F`, eager loading, bulk ops, `values()`, `atomic()`, … (see [docs/orm-features.md](docs/orm-features.md)) | Hiding SQLAlchemy for complex queries — it's always one import away |
| Migrations (Alembic, convention-driven) | Templates, static files (next up — see [roadmap](docs/roadmap.md)) |
| Shell, runserver, test integration | Replacing FastAPI routing or Pydantic |
| Admin, general auth, REST API — opt-in via `INSTALLED_APPS` | CSRF tokens beyond `SameSite=Lax`, per-object permissions |
| Opt-in, per-model permissions (`ModelAdmin.enforce_permissions`) | `ManyToManyField(through=...)` (deferred) |

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

Documentation: [fast-frame.readthedocs.io](https://fast-frame.readthedocs.io/). Source of that site is `mkdocs.yml` and `.readthedocs.yaml`.

## Documentation

| Document | Description |
| --- | --- |
| [Vision & thesis](docs/vision-and-thesis.md) | Product direction and positioning |
| [Design principles](docs/design-principles.md) | How we make tradeoffs |
| [Architecture](docs/architecture.md) | Components and dependencies |
| [MVP v0.1](docs/mvp-v0.1.md) | First release scope and success criteria |
| [Roadmap](docs/roadmap.md) | Direction beyond the first release |
| [Non-goals](docs/non-goals.md) | What we explicitly drop or defer |
| [App contract](docs/app-contract.md) | Installed apps and extension points |
| [ORM features](docs/orm-features.md) | `Q`/`F`, eager loading, bulk ops, `values()`, `atomic()`, … |
| [Session lifecycle](docs/session-lifecycle.md) | DB session rules |
| [Public API](docs/public-api-v0.1.md) | Stable surface (v0.1) |
| [Shell](docs/shell.md) | Stdlib REPL, `SHELL_IMPORTS`, startup script |
| [Repository layout](docs/repository-layout.md) | This repo and future package structure |
| [Contributing](CONTRIBUTING.md) | How to participate |

Architecture decisions are recorded in [docs/adr/](docs/adr/).

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
