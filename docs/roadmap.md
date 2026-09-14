# Roadmap

High-level direction after v0.1. Dates and ordering may change.

```text
                    FastFrame
                        │
                        ▼
                     v0.1  ←  core loop (this repo's first implementation target)
                        │
                        ▼
                     v0.2
                        │
             Better developer experience
                        │
                        ▼
                     v0.3  →  Admin (optional app)
                        │
                        ▼
                     v0.4  →  Auth / permissions
                        │
                        ▼
                     v0.5  →  Templates / static
                        │
                        ▼
                     v0.6+ →  Tasks, cache, email, storage, …
                        │
                        ▼
                     v1.0  →  production-ready platform (checks, docs, stability)
```

## v0.2 — Developer experience

- Richer routing conventions and dependency integration
- Improved configuration patterns
- Testing improvements (fixtures, DB isolation)
- Application lifecycle hooks
- CLI polish
- Health and `check` commands

## v0.3 — Admin

Optional Django-admin-like interface:

- Model registration
- CRUD, search, filtering, pagination
- Authentication hooks
- Customization without forcing admin on every project

## v0.4 — Authentication and authorization

Potential optional app:

- Users, password auth, sessions
- Permissions, groups/roles
- Middleware / dependencies for FastAPI

## v0.5 — Templates and static files

- Jinja2 templates and discovery
- Static file handling and collectstatic for production

## v0.6+ — Additional batteries

Background tasks, email, caching, storage, signals/events, custom management commands ecosystem, observability, production checks, deployment helpers.

## v1.0 — Production-ready platform

Stable public API, migration story, documentation, and operational commands (`check --deploy`, migrate, collectstatic) that teams trust for production.
