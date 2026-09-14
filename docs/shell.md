# Shell

FastFrame uses the **standard library Python REPL** only (`code.interact`). There is no built-in IPython or ptpython integration.

## What loads automatically

On `python manage.py shell`:

1. Settings and database session are initialized.
2. Unless disabled, **all model classes** from each installed app’s `models.py` are added to the namespace (e.g. `User`).
3. Optional **`SHELL_IMPORTS`** lines from settings are executed.
4. Optional **`config/shell_startup.py`** (or **`SHELL_STARTUP`**) is executed.
5. Optional **`AppConfig.shell(context)`** hooks run for each installed app.

Always available: `settings`, `session`.

## Settings

```python
# config/settings.py

# Default True — expose Model subclasses from each app's models.py
SHELL_AUTO_IMPORT_MODELS = True

# Each string is executed in the shell namespace (one import statement per line)
SHELL_IMPORTS = [
    "from fastframe.db.session import session_scope",
    "from billing import utils",
]

# Optional path relative to BASE_DIR (default: config/shell_startup.py if that file exists)
SHELL_STARTUP = "config/shell_startup.py"
```

## Startup script

`config/shell_startup.py` is normal Python run in the same namespace as the REPL:

```python
"""Custom shell imports and helpers."""

from users.models import User
from billing.utils import format_money

def active_users():
    return User.objects.filter(is_active=True)
```

Anything you define here (`User`, `format_money`, `active_users`, …) is available in the shell.

## Per-app hook

```python
# users/apps.py
from fastframe.core.apps import AppConfig


class UsersConfig(AppConfig):
    name = "users"

    def shell(self, context: dict) -> None:
        from users.models import User

        context["User"] = User
```

Use this for reusable packages; project-specific imports fit better in `SHELL_IMPORTS` or `shell_startup.py`.

## Session behavior

The shell keeps one database session open for the REPL session. Commits are applied when you exit cleanly; Ctrl-C rolls back. Use `session.commit()` explicitly when you want to persist changes mid-session.
