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
