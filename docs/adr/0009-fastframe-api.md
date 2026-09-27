# ADR 0009: FastFrameAPI as an additive routing facade

## Status

Accepted

## Context

Newcomers want a shorter path to an endpoint than a hand-wired `APIRouter`. Experienced users already know FastAPI and must not have to unlearn it. ADR 0002 forbids a parallel request stack and Django-style views.

## Decision

- Add `FastFrameAPI`, a facade over `APIRouter`. `get` / `post` / `put` / `patch` / `delete` register functions. `route(path)` registers a class whose methods are named after HTTP verbs.
- The path is always explicit. A class name is never a URL. Methods that are not HTTP verbs are not endpoints.
- Returned `Model` instances and `QuerySet`s serialize to JSON-safe dicts. Pydantic models, `response_model`, and `Depends` stay FastAPI's.
- A native `APIRouter` remains valid. `FastFrameAPI.include_router` mounts one. Installed apps may also export `api` from `<app>.api`, which is mounted beside `urls.py` routers.
- FastFrame does not build a second OpenAPI system.

## Consequences

- FastAPI docs still apply. The facade is additive.
- Automatic path inference, and turning arbitrary methods into endpoints, stay rejected unless a later ADR supersedes this one.
- Serialization is the common case (field dicts). A custom response shape still needs an explicit `response_model` or a hand-built dict.
