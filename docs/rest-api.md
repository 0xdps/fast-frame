# REST API (token-authenticated, generic CRUD)

An opt-in, second way to reach the models you've already registered with
`admin_site` — for non-browser clients (mobile apps, scripts, third-party
integrations) that can't carry a session cookie. It's the same
list/get/create/update/delete engine the admin API uses
(`fastframe.admin.api._build_crud_router`), just authenticated with a
bearer token instead of a cookie, and open to **any active user** rather
than only `can_access_admin` users.

## Enabling it

```python
# settings.py
ENABLE_REST_API = True
```

```python
# app.py
from fastframe.api import include_rest_api

app = create_app()
include_rest_api(app)  # create_app() also does this automatically when
                        # ENABLE_REST_API is set, before it returns
```

Off by default — registering a model for admin doesn't expose it here
until you opt in.

## Obtaining a token

```http
POST /api/auth/token
Content-Type: application/json

{"username": "alice", "password": "...", "name": "mobile app"}
```

```json
{"data": {"token": "9f8c...64 hex chars"}}
```

The raw token is shown **exactly once**. Only its SHA-256 hash is stored
(`fastframe.contrib.auth.tokens.Token`) — if it's lost, revoke it and get a
new one. A user can hold multiple tokens (e.g. one per device); creating a
new one doesn't invalidate the others.

## Using it

```http
GET /api/v1/post
Authorization: Bearer 9f8c...
```

Same endpoints, same response shapes as the admin API (see
`fastframe.admin.api`'s module docstring) — just under `API_PREFIX`
(default `/api/v1`) instead of `ADMIN_API_PREFIX`:

```
GET    /api/v1/schema
GET    /api/v1/{resource}
GET    /api/v1/{resource}/{id}
POST   /api/v1/{resource}
PUT    /api/v1/{resource}/{id}
DELETE /api/v1/{resource}/{id}
DELETE /api/v1/{resource}?ids=a&ids=b
GET    /api/v1/{resource}/choices/{field}
```

## Revoking a token

```http
DELETE /api/auth/token
Authorization: Bearer 9f8c...
```

Revokes the token used to make *this* request (404 if it's already gone).

## Permissions

Any active user (`is_active`) may authenticate — there's no `can_access_admin`
requirement here. Per-model permissions still come from each model's
`ModelAdmin` (`has_add_permission`, `has_change_permission`,
`has_delete_permission`, `has_view_permission`), since both surfaces share
the same registry. There's no per-user/per-object permission model yet —
see the v0.4 entry in [roadmap.md](roadmap.md).

**Consequence to be aware of:** because this reuses the admin registry,
any model registered for the admin becomes reachable from the REST API too
once you enable it — including `AuditLog` (read-only, but readable by any
active user, not just admins). Don't enable `ENABLE_REST_API` on a project
where that's not acceptable without first tightening `has_view_permission`
on sensitive models.

## Audit log

Every create/update/delete made through this API is recorded in
`AuditLog` (`source="api"`), exactly like the admin API (`source="admin"`)
— see [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md).
