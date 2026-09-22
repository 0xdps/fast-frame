# CLI

FastFrame uses a **two-level CLI**, similar in spirit to Django's `django-admin` vs `manage.py`.

## Global: `fastframe`

Used **before** a project exists or from outside the project tree.

Primary job in v0.1:

```text
fastframe startproject myproject
```

Creates:

- Project directory with `manage.py`, `config/`, built-in `health` app, and `tests/`
- `pyproject.toml` depending on `fastframe`

Install via:

```text
pip install fastframe
```

(When published; not yet on PyPI during scaffolding phase.)

## Project-local: `manage.py`

Used **inside** a generated project. Bootstraps FastFrame (settings, apps, database) before dispatching commands.

Examples:

```text
python manage.py runserver
python manage.py shell
python manage.py makemigrations
python manage.py migrate
python manage.py test
python manage.py check
python manage.py startapp users
```

### `runserver` address/port

Django-style single positional argument, not `--host`/`--port` flags:

```text
python manage.py runserver            # 127.0.0.1:8000 (default)
python manage.py runserver 8080       # 127.0.0.1:8080 (bare port)
python manage.py runserver 0.0.0.0    # 0.0.0.0:8000 (bare host)
python manage.py runserver 0.0.0.0:8080
python manage.py runserver --reload   # auto-reload for development
```

### `check`

Runs structural checks (settings shape, duplicate app labels, `DATABASE_URL`
presence) plus every installed app's `AppConfig.checks()` hook, and prints
each result as `LEVEL: obj: id: message` (with an optional `HINT:` line).
Exits `1` if any `ERROR`/`CRITICAL` message was found — safe to use as a CI
gate.

```text
python manage.py check              # structural checks only, no I/O
python manage.py check --database   # + DB connectivity + pending migrations
```

`--database` opts into checks that require a live database connection
(connectivity, and comparing Alembic's migration heads against what's
actually applied). It's opt-in, not the default, so a plain `check` stays
fast and safe to run before a database even exists — matching Django's
`check --database` precedent.

Apps add their own checks via `AppConfig.checks()`:

```python
from fastframe.core.checks import CheckMessage, WARNING

class BillingConfig(AppConfig):
    def checks(self) -> list[CheckMessage]:
        if not getattr(settings, "STRIPE_KEY", None):
            return [CheckMessage(level=WARNING, message="STRIPE_KEY not set.")]
        return []
```

### `test` and forwarding args to pytest

`manage.py test` wraps `pytest.main()`. Because of how Python's `argparse`
handles remainder arguments, flags meant for pytest must come **after `--`**:

```text
python manage.py test                    # runs `pytest tests`
python manage.py test -- -v              # verbose
python manage.py test -- -k health       # keyword filter
python manage.py test -- tests/test_todos.py -v
```

Omitting `--` before pytest flags (e.g. `manage.py test -v`) raises
`unrecognized arguments`.

## Bootstrap behavior

Every command that needs the app context should:

1. Resolve project root and settings module.
2. Initialize the FastFrame application registry.
3. Load `INSTALLED_APPS` and run `AppConfig.ready()` where applicable.
4. Initialize database connectivity when required for that command.

Commands like `runserver` and `shell` need full initialization; `startapp` may need less.

## Extensibility

Third-party and local apps register commands under:

```text
<app>/management/commands/<command_name>.py
```

Exact discovery mechanism TBD; path follows Django familiarity.

## Future

- `check --deploy`
- `collectstatic` when static files exist
