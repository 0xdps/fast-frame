# Authentication user model

FastFrame ships a user model and lets a project replace it, the same way
Django's `AUTH_USER_MODEL` works.

## Built-in user

`fastframe.contrib.auth.models.User` stores:

| Field | Role |
| --- | --- |
| `username`, `email` | Unique identity |
| `first_name`, `last_name` | Display name |
| `password` | PBKDF2 hash, write-only in the admin API |
| `is_active` | Account can log in |
| `user_data` | JSON for admin access, permissions, preferences |
| `date_joined`, `last_login` | Timestamps |

There are no `is_staff` or `is_superuser` columns. Put those flags in
`user_data`:

```python
user.user_data = {
    "admin_access": True,
    "superuser": True,
    "permissions": ["blog.add_post"],
    "preferences": {"theme": "dark"},
}
```

Helpers on the model: `can_access_admin`, `is_superuser`, `permissions`,
`has_permission()`, `set_password()`, `check_password()`.

`user_data` is the column name because SQLAlchemy reserves `metadata` on
declarative models.

## Passwords

`user.set_password(raw_password)` hashes with PBKDF2-SHA256
(`fastframe.contrib.auth.hashers`) and, by default, validates strength
first (`PASSWORD_MIN_LENGTH`, and rejects a password equal to the
username, case-insensitively) via
`fastframe.contrib.auth.validators.validate_password_strength`, raising
`ValidationError` on failure:

```python
user.set_password("short")  # raises ValidationError if shorter than PASSWORD_MIN_LENGTH
user.set_password("x", validate=False)  # escape hatch — skips the check
```

`check_password()` compares hashes with `hmac.compare_digest` (constant
time) rather than `==`, and `fastframe.contrib.auth.authenticate()` always
hashes against a dummy value even when the username doesn't exist or the
account is inactive — both close a timing side-channel that would
otherwise let an attacker learn which usernames exist by measuring
response time.

## Groups and permissions

`fastframe.contrib.auth.models.Group` is a plain model (`name`, unique;
`permissions`, a flat JSON list of permission strings) with a
many-to-many `User.groups` relationship. See [permissions.md](permissions.md)
for the full permission-string format and how `ModelAdmin.enforce_permissions`
uses it. `Group` is registered in the admin (`GroupAdmin`) like any other
model.

## Session revocation

Every `User` has a `session_version` (an integer, starts at `0`, stored in
`user_data`) that's embedded in the signed session cookie payload
alongside the user id. Every request re-checks the cookie's `session_version`
against the user's *current* one — if they don't match, the session is
treated as logged out (`401`).

```python
user.invalidate_sessions()  # bumps session_version; every existing cookie for
user.save()                  # this user now fails verification, everywhere
```

This gives server-side "log out everywhere" / forced-logout semantics
without a session table — useful after a password change or a suspected
compromised cookie. There's no cost to calling it defensively (e.g. in a
"change password" or "revoke all sessions" account-settings action).

## General-purpose session auth (outside `/admin`)

`POST /api/auth/login`, `POST /api/auth/logout`, and `GET /api/auth/me`
(mounted automatically by `create_app()` when `ENABLE_AUTH_API` is `True`,
the default) give any app route the same signed-cookie login the admin
uses — without requiring `can_access_admin`. It's the *same* cookie
(`ff_admin_session`), so a user who's logged into `/admin` is already
logged in for these routes too, and vice versa.

```http
POST /api/auth/login
Content-Type: application/json

{"username": "alice", "password": "..."}
```

Use the dependencies directly in your own routers:

```python
from fastapi import Depends
from fastframe.contrib.auth.dependencies import get_current_user, login_required, permission_required

@router.get("/profile")
def profile(user = Depends(login_required)):
    return user  # a dict snapshot: id, username, email, is_active,
                 # is_superuser, can_access_admin, permissions

@router.get("/reports")
def reports(user = Depends(permission_required("reports.view_report"))):
    ...

@router.get("/maybe-personalized")
def maybe(user = Depends(get_current_user)):
    ...  # `user` is None if not logged in — no 401 raised
```

`login_required` raises `401` if there's no valid session;
`permission_required(perm)` raises `401` (not logged in) or `403` (logged
in, missing the permission — superusers always pass); `get_current_user`
returns `None` rather than raising, for routes that behave differently for
anonymous vs. logged-in users instead of requiring login outright.

Login attempts on `/api/auth/login` (and `/api/admin/login`, and
`/api/auth/token`) are rate-limited — see [settings.md](settings.md#rate-limiting).

Set `ENABLE_AUTH_API = False` to omit these routes entirely (e.g. if a
project wants only its own auth, or only the admin's).

## Referencing the active user model

```python
from fastframe.contrib.auth import get_user_model

User = get_user_model()
```

`get_user_model()` reads `AUTH_USER_MODEL` (default `"auth.User"`).

## Replacing the user model

Point settings at your own class before that class is imported:

```python
AUTH_USER_MODEL = "accounts.CustomUser"
```

See `examples/custom_user/`. The model needs `username`, `email`, `password`,
`is_active`, `user_data`, and `set_password()` so `manage.py createadminuser`
can create an account.

```text
python manage.py createadminuser
```

The command hashes the password, sets `user_data.admin_access` and
`user_data.superuser`, and creates tables for models already imported.

## Primary keys

`DEFAULT_AUTO_FIELD` chooses the `id` column when a model does not declare one:

| Value | Column |
| --- | --- |
| `AutoField` | integer, database autoincrement |
| `BigAutoField` | 64-bit integer |
| `UUIDField` | UUID version 7 |

UUID fields are always version 7 (time-ordered). Generation is Python-side by
default (`UUID_GENERATION = "python"`), which works on SQLite, PostgreSQL, and
MySQL. Python older than 3.14 uses the `uuid-utils` package. Database-side
generation (`UUID_GENERATION = "database"`) expects a `uuid_generate_v7()`
function, such as the `pg_uuidv7` extension.
