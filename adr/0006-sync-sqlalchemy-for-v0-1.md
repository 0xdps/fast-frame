# ADR 0006: Sync SQLAlchemy for v0.1

## Status

Accepted

## Context

FastAPI supports async routes; SQLAlchemy supports both sync and async engines. Choosing a default for v0.1 affects session lifecycle, `get_session`, and migration tooling.

## Decision

- v0.1 uses **synchronous SQLAlchemy** only (`create_engine`, `Session`).
- HTTP handlers may be `def` or `async def`; ORM access in v0.1 examples uses **sync** sessions via `Depends(get_session)`.
- Async SQLAlchemy and async session dependencies are **deferred** to a later release.

## Consequences

- Simpler session and transaction boundaries for the first loop.
- Documentation must note limitations for async-heavy apps until async ORM lands.
- `get_session` is a sync generator dependency (or sync yield pattern compatible with FastAPI).
