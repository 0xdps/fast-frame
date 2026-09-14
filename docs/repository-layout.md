# Repository layout

This document describes the **FastFrame framework repository** (`0xdps/ff`) and the planned **Python package layout** once implementation begins.

## Current phase (documentation only)

No `src/fastframe` implementation yet. The repo contains metadata, docs, and ADRs.

```text
ff/                          # git repository root (short name)
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── CHANGELOG.md
├── pyproject.toml
├── .gitignore
├── docs/                    # product & technical documentation
├── adr/                     # architecture decision records
├── .github/                 # issue/PR templates, CI (when added)
└── (future) src/fastframe/  # framework package — not created yet
```

## Planned framework package layout (implementation)

Target: **src layout** with Hatchling (see `pyproject.toml`).

```text
src/
└── fastframe/
    ├── __init__.py
    ├── __version__.py
    ├── cli/
    │   ├── __init__.py
    │   ├── main.py              # fastframe entry
    │   └── management/          # shared command utilities
    ├── core/
    │   ├── __init__.py
    │   ├── apps.py              # AppConfig, registry
    │   ├── lifecycle.py         # bootstrap
    │   └── checks.py            # check command (later)
    ├── conf/
    │   ├── __init__.py
    │   └── settings.py          # settings loading helpers
    ├── http/
    │   ├── __init__.py
    │   └── asgi.py              # get_asgi_application
    ├── db/
    │   ├── __init__.py
    │   ├── session.py           # get_session
    │   └── engine.py
    ├── models/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── fields.py            # ergonomic field helpers (TBD)
    │   └── manager.py
    ├── migrations/
    │   ├── __init__.py
    │   └── ...                  # Alembic integration
    ├── contrib/
    │   └── ...                  # optional in-repo apps (e.g. orm, health)
    └── project_template/        # files copied by startproject
        ├── manage.py
        ├── pyproject.toml
        └── config/
            └── ...

tests/
├── unit/
├── integration/
└── conftest.py

examples/                        # optional: minimal demo project for CI
└── demo_project/
```

Exact module names may change; boundaries should stay:

- **cli** — entrypoints
- **core** — apps and lifecycle
- **http** — FastAPI wiring only
- **db / models / migrations** — data layer
- **project_template** — generated user projects

## Generated user project (reference)

See [architecture.md](architecture.md). Not stored in this repo except as templates under `project_template/`.

## Naming

| Name | Meaning |
| --- | --- |
| `ff` | GitHub repository directory name |
| `fastframe` | PyPI / import package name |
| FastFrame | Product name |
