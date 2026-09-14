# Architecture Decision Records

We use ADRs to capture significant technical decisions: context, decision, and consequences.

## Format

- One file per decision: `NNNN-short-title.md`
- Status: Proposed | Accepted | Deprecated | Superseded

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-fastapi-as-http-layer.md) | FastAPI as the HTTP layer | Accepted |
| [0003](0003-thin-orm-with-sqlalchemy-escape-hatch.md) | Thin ORM with SQLAlchemy escape hatch | Accepted |
| [0004](0004-dual-cli-fastframe-and-manage-py.md) | Dual CLI: fastframe and manage.py | Accepted |
| [0005](0005-extensibility-via-installed-apps.md) | Extensibility via installed apps | Accepted |
| [0006](0006-sync-sqlalchemy-for-v0-1.md) | Sync SQLAlchemy for v0.1 | Accepted |

When superseding an ADR, link the old and new records and update this index.
