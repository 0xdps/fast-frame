# ADR 0004: Dual CLI — fastframe and manage.py

## Status

Accepted

## Context

`python manage.py startproject` requires an existing `manage.py`, which new users do not have. Django uses `django-admin` for bootstrapping.

## Decision

- **`fastframe`** — global console script installed with the package; at minimum `startproject`.
- **`manage.py`** — project-local entry point for runserver, shell, migrations, test, check, startapp.

## Consequences

- Documentation and tutorials must show `fastframe startproject` first, then `manage.py` inside the project.
- Two code paths share bootstrap utilities in the framework CLI module.
