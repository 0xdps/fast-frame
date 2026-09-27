# ADR 0003: Thin ORM with SQLAlchemy escape hatch

## Status

Accepted

## Context

Django-like ergonomics suggest `Model.objects.filter(...)`, but a full QuerySet implementation is large and competes with SQLAlchemy.

## Decision

- Models are **SQLAlchemy mapped classes** with a **thin manager**. FastFrame owns model **discovery** and **migration integration** (Alembic), not a second query algebra.
- **Complex queries** use SQLAlchemy directly with the project's session.
- Accepted manager surface, as of v0.1.0: `filter` / `exclude` / `order_by` / `limit` / `offset`, `get` / `first` / `count` / `exists`, `create` / `save` / `delete`, Django-style field lookups, `Q()` / `F()`, `select_related()` / `prefetch_related()` on declared relations, `bulk_create()` / `bulk_update()` and queryset `update()` / `delete()`, `get_or_create()` / `update_or_create()`, `values()` / `values_list()`, `only()` / `defer()`, and `atomic()`. See [docs/orm-features.md](../orm-features.md).
- Not accepted, until an ADR supersedes this one: `annotate()`, subquery composition, window functions, `ManyToManyField(through=...)`, and a FastFrame-branded `select()`.

## Consequences

- Documentation must show the escape hatch early to set expectations.
- Django migrants may need to learn SQLAlchemy for advanced cases — acceptable tradeoff.
- A new ORM method is either a thin alias of something already in the accepted list, or it waits for an ADR that supersedes this one. A feature page cannot extend the list by itself.
