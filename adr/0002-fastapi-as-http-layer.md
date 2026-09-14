# ADR 0002: FastAPI as the HTTP layer

## Status

Accepted

## Context

FastFrame is built on FastAPI. We must decide whether to introduce a Django-like view layer or expose FastAPI directly inside projects.

## Decision

- **Do not** implement Django-style views, CBVs, or a parallel request/response stack.
- **Do** discover and mount FastAPI routers from installed apps.
- **Do** use Pydantic and `Depends` as in standard FastAPI applications.
- FastFrame wraps **integration** (ASGI app factory, session dependency), not FastAPI's public routing API.

## Consequences

- FastAPI documentation and examples remain largely applicable.
- We avoid maintaining a shadow HTTP API.
- Template-driven HTML views are deferred to an optional component (v0.5+).
