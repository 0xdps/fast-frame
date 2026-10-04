# Repository layout

This document describes the **FastFrame framework repository** ([0xdps/fast-frame](https://github.com/0xdps/fast-frame)) and the **Python package layout**, as of package release 0.1.3.

## Repository root

```text
fast-frame/
├── README.md, LICENSE, CONTRIBUTING.md, CHANGELOG.md, SECURITY.md
├── pyproject.toml
├── docs/                    # product & technical documentation (this file included)
├── docs/adr/                # architecture decision records
├── .github/                 # issue/PR templates, CI workflow
├── examples/
│   └── todo_app/            # real end-to-end app built with the v0.1 loop
├── src/fastframe/           # the framework package (see below)
└── tests/                   # framework's own test suite + integration fixture
```

## Framework package layout (`src/fastframe/`)

Target: **src layout** with Hatchling (see `pyproject.toml`).

```text
src/fastframe/
├── __init__.py
├── __version__.py
├── cli/
│   ├── main.py               # `fastframe` entry (startproject, version)
│   ├── manage.py             # `manage.py` command dispatcher
│   ├── scaffold.py           # project/app template rendering
│   └── commands/             # runserver, check, makemigrations, migrate,
│                              # showmigrations, dbshell, shell, test,
│                              # startapp, createadminuser, startadmin, buildadmin
├── conf/
│   └── global_settings.py     # default settings values
├── core/
│   ├── apps.py                # AppConfig, AppsRegistry, populate_apps()
│   ├── bootstrap.py           # bootstrap(), get_apps_registry(), reset_bootstrap()
│   ├── settings.py            # loads the project settings module
│   └── checks.py              # CheckMessage, run_checks(); backs `manage.py check`
├── http/
│   └── asgi.py                 # get_asgi_application(), session middleware,
│                                # DoesNotExist/MultipleObjectsReturned handlers
├── db/
│   ├── engine.py               # get_engine() from DATABASE_URL
│   ├── session.py              # get_session, session_scope, begin/end_session
│   └── init.py                 # create_tables() (dev/test convenience)
├── models/
│   ├── base.py                  # Model (DeclarativeBase) with `objects`, save/delete
│   ├── fields.py                # declarative fields (CharField, ForeignKey, ...)
│   ├── manager.py               # Manager + QuerySet (filter/exclude/order_by/...)
│   ├── query.py                 # Q(), F(), lookups
│   └── exceptions.py            # DoesNotExist, MultipleObjectsReturned
├── admin/                       # opt-in Tailwind UI + /api/admin
├── api/                         # opt-in token CRUD at /api/v1
├── contrib/auth/                # User, Group, session auth
├── health/                      # GET /health; on by default in a new project
├── docs/                        # opt-in Swagger (/docs, /redoc, /openapi.json)
├── middleware/                  # CORS and security headers
├── migrations/
│   ├── paths.py, runner.py, runtime.py   # Alembic integration
│   └── templates/                        # env.py / script.py.mako for new projects
├── shell/
│   └── context.py               # build_shell_namespace() for `manage.py shell`
├── project_template/            # files copied by `fastframe startproject`
    ├── manage.py, pyproject.toml
    ├── config/                   # settings.py, urls.py, asgi.py, migrations/
    └── tests/                    # conftest.py (project_env, client fixtures), test_health.py
```

Module boundaries to preserve:

- **cli** — entrypoints and command dispatch only; delegates real work to other modules.
- **core** — settings loading, app registry, lifecycle (`bootstrap`), checks.
- **http** — FastAPI/ASGI wiring only.
- **db / models / migrations** — the data layer.
- **project_template** — what gets copied into a *generated user project*; not imported by the framework itself at runtime.

## Not (yet) present

Still not built:

- Custom management command auto-discovery (`<app>/management/commands/`) — planned (see [app-contract.md](app-contract.md), [roadmap.md](roadmap.md)).

`conf/global_settings.py` holds defaults. `core/settings.py` loads the project settings module. `fastframe.contrib.auth` and `models/fields.py` exist. Earlier drafts of this file said they did not.

## Naming

| Name | Meaning |
| --- | --- |
| `fast-frame` | GitHub repository name |
| `fastframe` | PyPI / import package name |
| FastFrame | Product name |
