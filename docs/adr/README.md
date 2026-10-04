# Architecture Decision Records

We use ADRs to capture significant technical decisions: context, decision, and consequences.

## Format

- One file per decision: `NNNN-short-title.md`
- Status: Proposed | Accepted | Deprecated | Superseded
- When the implementation moves without rejecting the decision, append an Addition dated at the top. Leave the original context, decision, and consequences in place. Supersede the ADR only when the decision itself no longer holds.

## Index

| ADR | Title | Status |
| --- | --- | --- |
| [0001](0001-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0002](0002-fastapi-as-http-layer.md) | FastAPI as the HTTP layer | Accepted |
| [0003](0003-thin-orm-with-sqlalchemy-escape-hatch.md) | Thin ORM with SQLAlchemy escape hatch | Accepted |
| [0004](0004-dual-cli-fastframe-and-manage-py.md) | Dual CLI: fastframe and manage.py | Accepted |
| [0005](0005-extensibility-via-installed-apps.md) | Extensibility via installed apps | Accepted |
| [0006](0006-sync-sqlalchemy-for-v0-1.md) | Sync SQLAlchemy for v0.1 | Accepted |
| [0007](0007-ssr-for-admin-v0-3.md) | Server-side rendering for admin (v0.3) | Superseded by 0008 |
| [0008](0008-rest-api-react-admin.md) | REST API + React admin | Accepted; Addition records the move off React Admin |
| [0009](0009-fastframe-api.md) | FastFrameAPI routing facade | Accepted |
| [0010](0010-curated-reexports.md) | Curated re-exports, not wrapped engines | Accepted |
| [0011](0011-admin-sidebar-stays-expanded.md) | Admin sidebar stays expanded | Accepted |

When superseding an ADR, link the old and new records and update this index.
