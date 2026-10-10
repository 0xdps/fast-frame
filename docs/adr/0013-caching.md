# ADR 0013: Caching

## Status

Proposed. Not implemented.

## Addition (2026-10-07)

Templates are out of scope, including template fragment caching. See the Addition on [ADR 0002](0002-fastapi-as-http-layer.md). This withdraws the Context sentence below that calls templates "the next unbuilt product phase," and the Consequences bullet that says this ADR "does not pull caching ahead of templates." There is no template phase to wait on, implemented or not — only signals and observability stay ahead of this in the plan.

## Context

Background jobs ([ADR 0012](0012-background-jobs.md)) and app `manage.py` commands are in place. Templates and static files are still the next unbuilt product phase. Caching was left on the later list, next to signals and observability, with no shape of its own.

A FastFrame project can run more than one API process. A cache that exists only inside one process does not help those processes share a computed value. The rate limiter is already documented as single-process on purpose ([docs/ADMIN_SECURITY_WARNING.md](../ADMIN_SECURITY_WARNING.md)). This ADR does not move it.

[ADR 0010](0010-curated-reexports.md) says FastFrame wraps a library where it owns lifecycle, and leaves the library alone otherwise. The cache lifecycle is small: which store, a key prefix, a default timeout, and JSON so every process reads what another process wrote. Redis is the store operators already run for Celery. Celery's broker uses Redis database 0 by default. The cache wants its own URL so clearing cached values cannot delete the queue.

## Decision

### An optional app

`fastframe.cache`, mounted only when it is listed in `INSTALLED_APPS`. A new project does not include it. The base `fast-frame` package does not depend on Redis. `pip install "fast-frame[cache]"` installs the Redis client for a Redis URL. The in-process backend needs no extra.

Importing the cache when the app is not installed fails with a message that names `INSTALLED_APPS`. A missing cache does not silently succeed.

### One cache

There is one cache object.

```python
from fastframe.cache import cache

cache.set("report:1", {"total": 3}, timeout=60)
cache.get("report:1")
```

`get` returns the value, or `None` when the key is absent. A stored JSON `null` also comes back as `None`. Callers store a real value when they need to tell those apart.

`set` stores a value. `add` stores it only when the key is absent and returns whether it stored it. `delete` removes one key. `get_or_set` returns the stored value, or calls a zero-argument function, stores that result, and returns it. `clear` removes every key under this project's prefix.

Keys are non-empty strings. Values must be JSON-serializable. FastFrame does not pickle cache values.

`get_or_set` does not take a lock. Two processes can both compute the same missing key. A lock is later work.

The API is synchronous, in line with the sync ORM ([ADR 0006](0006-sync-sqlalchemy-for-v0-1.md)).

There is no second named cache, no `incr`, and no cache version field. Changing `CACHE_KEY_PREFIX` is how a project drops a generation of keys.

### The store

`CACHE_URL` picks the backend.

| URL | Backend |
| --- | --- |
| `redis://localhost:6379/1` | Redis. This is the default. Database 1 stays off Celery's default database 0. `rediss://` and `unix://` are Redis URLs too. |
| `locmem://` | A dict in this process, guarded by a lock. Tests use this. Another API process has its own dict. |

`CACHE_KEY_PREFIX` defaults to `"fastframe"`. The stored key is `{prefix}:{key}`. `clear` deletes that prefix only. It does not flush the Redis database.

`CACHE_DEFAULT_TIMEOUT` defaults to `300` seconds. `timeout=None` stores the value with no expiry. `timeout=0` does not store it.

`manage.py check` reports `cache.E001` when the app is installed and `CACHE_URL` is empty. `locmem://` skips that check.

`python manage.py clearcache` is a command on this app. It runs `cache.clear()`.

### Out of scope

- HTTP cache headers and a view decorator.
- Template fragment caching. FastFrame will not ship templates.
- Caching query results inside the ORM.
- Moving the login rate limiter onto this cache.
- Memcached, a database table, or a file backend.
- A general backend plugin API. A third store can be added later by a new URL scheme. [ADR 0005](0005-extensibility-via-installed-apps.md) stays as it is for everything else.

## Consequences

- Several API processes share one Redis cache. A `locmem://` cache does not cross a process boundary.
- The cache URL and the Celery broker URL are different settings. The defaults use different Redis databases.
- Tests set `CACHE_URL = "locmem://"` and do not start Redis.
- Signals and observability stay planned. This ADR does not pull caching ahead of templates. Implementation starts when that work is picked up.
- The rate limiter stays in-process until a later change stores it here.
