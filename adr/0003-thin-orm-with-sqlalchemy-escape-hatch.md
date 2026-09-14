# ADR 0003: Thin ORM with SQLAlchemy escape hatch

## Status

Accepted

## Context

Django-like ergonomics suggest `Model.objects.filter(...)`, but a full QuerySet implementation is large and competes with SQLAlchemy.

## Decision

- Models are **SQLAlchemy mapped classes** with a **thin manager** exposing a small method set: e.g. `filter`, `get`, `first`, `count`, `create`, `save`, `delete`.
- **Complex queries** use SQLAlchemy directly with the project's session.
- FastFrame owns model **discovery** and **migration integration** (Alembic), not a second query algebra in v0.1.

## Consequences

- Faster path to a trustworthy v0.1.
- Documentation must show the escape hatch early to set expectations.
- Django migrants may need to learn SQLAlchemy for advanced cases — acceptable tradeoff.
