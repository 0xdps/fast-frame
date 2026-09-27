# ADR 0010: Curated re-exports, not wrapped engines

## Status

Accepted

## Context

A new project otherwise starts with `fastapi`, `pydantic`, `sqlalchemy`, and `alembic` imports. That fights the "one framework" feel. Forking those libraries, or subclassing them so FastFrame can rename them, creates an API we would have to keep in sync with upstream docs and errors.

## Decision

- FastFrame owns a small import path. The underlying library owns the behavior.
- Imports are grouped by area. `from fastframe.http import FastFrameAPI`. `from fastframe.schemas import BaseModel, Field`. `from fastframe.models import Model`. The package root does not re-export these.
- `BaseModel` and `Field` are Pydantic's, re-exported from `fastframe.schemas`.
- They are the Pydantic objects. Not a subclass. Not `Schema` or `FastFrameSchema`.
- Anything not listed is imported from the original library. That is the escape hatch, not a gap to fill.
- A new re-export needs a reason a normal FastFrame app needs it often. `HTTPException` and `Depends` are not in this set, and there is no `fastframe.dependencies` module, until that reason exists.
- `fastframe.api` stays the optional token REST app. It is not the import path for `FastFrameAPI`.

## Consequences

- Tutorials can stay inside `fastframe` for the common request and response model.
- Pydantic's own docs still apply, because the class is Pydantic's.
- Renaming or wrapping `BaseModel` later would break this decision and needs a superseding ADR.
