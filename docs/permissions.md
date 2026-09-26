# Permissions

Django-style, per-request permissions for the admin API and the [general
REST API](rest-api.md) — opt-in, per model, backward compatible with the
static `has_*_permission` booleans that predate this.

## The model

There is no dedicated `Permission` table. Permissions are just strings,
shaped like Django's:

```
{app_label}.{action}_{model_name}
```

e.g. `"blog.change_post"`, `"shop.delete_widget"`. The four actions match
the four `ModelAdmin.has_*_permission` checks: `view`, `add`, `change`,
`delete`.

```python
from fastframe.contrib.auth.permissions import permission_codename

permission_codename(Post, "change")  # "blog.change_post"
```

Permission strings live in two places, both flat JSON lists:

- `User.permissions` — a user's own permissions.
- `Group.permissions` — permissions granted to every member of a group.

```python
from fastframe.contrib.auth.models import Group, User

with session_scope():
    editors = Group(name="editors")
    editors.permissions = ["blog.change_post", "blog.view_post"]
    editors.save()

    user = User.objects.get(username="alice")
    user.groups.add(editors)
    user.permissions = ["blog.delete_post"]  # plus a personal grant
    user.save()
```

`get_effective_permissions(user)` flattens a user's own permissions with
every group they belong to:

```python
from fastframe.contrib.auth.permissions import get_effective_permissions

get_effective_permissions(user)
# frozenset({"blog.change_post", "blog.view_post", "blog.delete_post"})
```

`user_has_perm(user, "blog.change_post")` and `user_has_model_perm(user,
Post, "change")` check membership in that set — except for superusers
(`user.is_superuser`), who pass every check unconditionally, and `None`
(unauthenticated), who pass none.

## Opt-in enforcement on `ModelAdmin`

By default, permission strings are inert. `ModelAdmin.has_*_permission`
behaves exactly as it always has — a static boolean, the same for every
user:

```python
class PostAdmin(ModelAdmin):
    has_delete_permission = False  # nobody can delete, ever — unchanged behavior
```

Set `enforce_permissions = True` to make the four checks per-request,
resolved against permission strings instead:

```python
class PostAdmin(ModelAdmin):
    enforce_permissions = True
```

With `enforce_permissions = True`, `model_admin.get_has_change_permission(user)`
(and the `view`/`add`/`delete` equivalents) now:

1. Returns `False` immediately if the static `has_change_permission`
   attribute is explicitly `False`. This is a **hard override** — even a
   user with the matching permission string is denied. Use it for fields
   or actions nobody should touch through the API, regardless of role.
2. Otherwise returns `True` for superusers.
3. Otherwise checks `user_has_model_perm(user, self.model, "change")`.

```python
class VaultAdmin(ModelAdmin):
    enforce_permissions = True
    has_delete_permission = False  # hard override: nobody, ever
```

Every admin API and REST API route (`list`, `get`, `create`, `update`,
`delete`, `choices`, and the schema endpoint) resolves permissions through
these `get_has_*_permission(user)` methods now, not the raw attributes
directly — so this is safe to flip per-model without touching route code.

**Backward compatibility:** `enforce_permissions` defaults to `False`.
Every existing `ModelAdmin` keeps its old, static, everyone-or-nobody
behavior until you explicitly opt a model in.

## `readonly_fields`, `fields`, `exclude`

These were previously only used for the admin UI's rendering — the API
never actually enforced them, so a client could still write a value for a
field marked `readOnly` in the schema. `get_editable_fields()` now filters
every create/update payload against `readonly_fields`/`fields`/`exclude`
before saving:

```python
class PostAdmin(ModelAdmin):
    readonly_fields = ["slug"]  # server-managed; silently dropped from payloads
```

A client that sends `{"title": "...", "slug": "custom"}` gets the `title`
applied and `slug` silently ignored — not a `400`, matching Django admin's
behavior for readonly fields. The schema (`GET /api/{admin|v1}/{resource}`
… `/schema`) also marks these fields `"readOnly": true` so well-behaved UIs
don't render an editable input for them in the first place.

## Checking permissions outside the admin/REST API

`fastframe.contrib.auth.dependencies.permission_required(perm)` is a
FastAPI dependency for any app route, session-cookie-authenticated — see
[auth.md](auth.md#general-purpose-session-auth-outside-admin).

```python
from fastframe.contrib.auth.dependencies import permission_required

@router.get("/reports", dependencies=[Depends(permission_required("reports.view_report"))])
def list_reports(): ...
```

## What's still not covered

- No per-object permissions (row-level) — only per-model.
- No per-field permissions beyond the binary `readonly_fields` cut.
- `ManyToManyField(through=...)` (custom columns on a join table, which
  would let `Group.permissions` be a real M2M to a `Permission` model
  instead of a flat JSON list) is deferred — see [roadmap.md](roadmap.md).
