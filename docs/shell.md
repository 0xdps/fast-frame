# Shell

`python manage.py shell` runs the standard library REPL (`code.interact`) by
default, but can launch `ptpython` or `IPython` instead for syntax
highlighting and autosuggestion — see "Interface" below.

## What loads automatically

On `python manage.py shell`:

1. Settings and database session are initialized.
2. Unless disabled, **all model classes** from each installed app’s `models.py` are added to the namespace (e.g. `User`).
3. Optional **`SHELL_IMPORTS`** lines from settings are executed.
4. Optional **`config/shell_startup.py`** (or **`SHELL_STARTUP`**) is executed.
5. Optional **`AppConfig.shell(context)`** hooks run for each installed app.

Always available: `settings`, `session`.

## Interface (syntax highlighting, autosuggestion)

The REPL itself is chosen *after* the namespace above is built, so models,
`session`, and anything from `SHELL_IMPORTS` / `shell_startup.py` / app
hooks are available no matter which one runs.

| `SHELL_INTERFACE` | Behavior |
| --- | --- |
| `"auto"` (default) | `ptpython` → `IPython` → standard library REPL, whichever is installed first |
| `"ptpython"` | Force `ptpython`. Errors out if not installed |
| `"ipython"` | Force `IPython`. Errors out if not installed |
| `"python"` | Force the standard library REPL — skip auto-detection entirely |

Neither `ptpython` nor `IPython` is a hard dependency. Install both with:

```bash
pip install fast-frame[shell]
```

...or just one (`pip install ptpython` / `pip install ipython`). With `auto`
(or no `ptpython`/`IPython` installed at all), you get the plain REPL — no
highlighting, no autosuggestion, same as before this setting existed.

`ptpython` is tried before `IPython` in `auto` mode because FastFrame turns
its autosuggestion on explicitly (it's off by default upstream) on top of
its default syntax highlighting. Modern `IPython` (8.12+) ships both
syntax highlighting and history-based autosuggestion on by default too —
either gets you the same result.

FastFrame also turns off IPython's default blank line before every
`In [n]:` prompt (`separate_in`, `"\n"` upstream) so the REPL stays as
dense as a normal terminal/the standard library REPL.

Override per-invocation without touching settings:

```bash
python manage.py shell -i ipython
python manage.py shell --interface python   # force the plain REPL for one run
```

`-i`/`--interface` takes priority over `SHELL_INTERFACE` when both are given.

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

# "auto" (default) tries ptpython, then IPython, then the standard library
# REPL. Pin to "ptpython", "ipython", or "python" to force one.
SHELL_INTERFACE = "auto"
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
