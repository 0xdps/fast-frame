# CLI

FastFrame uses a **two-level CLI**, similar in spirit to Django's `django-admin` vs `manage.py`.

## Global: `fastframe`

Used **before** a project exists or from outside the project tree.

Primary job:

```text
fastframe startproject myproject
```

Creates:

- Project directory with `manage.py`, `config/`, and `tests/`
- `pyproject.toml` depending on `fastframe`

Install the PyPI distribution `fast-frame`:

```text
pip install fast-frame
```

The import and the `fastframe` command use the name `fastframe`. `fastframe version` prints `fastframe.__version__`, which is still `0.1.0`. The package release in `pyproject.toml` is `0.1.3`.

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
python manage.py showmigrations
python manage.py dbshell
python manage.py startapp users
python manage.py createadminuser
python manage.py startadmin
python manage.py buildadmin
python manage.py work
python manage.py beat
python manage.py showtasks
python manage.py --version
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

### `showmigrations`

Lists every migration with an `[X]` (applied) / `[ ]` (pending) marker:

```text
python manage.py showmigrations
```

Migrations are grouped by the app that owns the file (see
[app-contract.md](app-contract.md)). Pair with `manage.py check --database`,
which surfaces the same "N unapplied migration(s)" fact as a one-line
warning suitable for CI.

### `dbshell`

Opens the native CLI for whatever `DATABASE_URL` points at (`sqlite3`,
`psql`, or `mysql`), with connection args pre-filled from the URL:

```text
python manage.py dbshell
```

Requires the corresponding client binary on `PATH`. Supported drivers:
`sqlite`, `postgresql`, `mysql`/`mariadb`.

### `test` and forwarding args to pytest

`manage.py test` forwards everything after `test` straight through to
`pytest.main()` — flags don't need `--` in front of them:

```text
python manage.py test                    # runs `pytest tests`
python manage.py test -v                 # verbose
python manage.py test -k health          # keyword filter
python manage.py test tests/test_todos.py -v
python manage.py test -- -k health       # `--` still accepted, stripped
```

Note: this is a deliberate special case in `manage.py`'s dispatch, not
plain `argparse` subparser behavior. `argparse` can't reliably pass
dash-prefixed tokens through a subparser's `nargs=REMAINDER` positional
immediately after the subcommand name, so `test`'s argv is intercepted and
forwarded before the top-level parser ever sees it — the same pattern
`git`/`npm` use for passthrough subcommands.

## Bootstrap behavior

Every command that needs the app context should:

1. Resolve project root and settings module.
2. Initialize the FastFrame application registry.
3. Load `INSTALLED_APPS` and run `AppConfig.ready()` where applicable.
4. Initialize database connectivity when required for that command.

Commands like `runserver` and `shell` need full initialization; `startapp` may need less.

### `work` and `beat`

Require `"fastframe.tasks"` in `INSTALLED_APPS` and `pip install "fast-frame[tasks]"`.

```text
python manage.py work       # Celery worker
python manage.py beat       # Celery Beat; enqueues periodic tasks, does not run them
python manage.py showtasks  # list Beat schedules and registered tasks
```

`--loglevel` defaults to `info` on `work` and `beat`. `showtasks` reads this process's configuration. It does not start a worker or Beat, and it does not connect to the broker. See [tasks.md](tasks.md).

### `createadminuser`

Creates a user from `AUTH_USER_MODEL` with `user_data.admin_access` and
`user_data.superuser` set. Prompts for username, email, and password unless
the flags are passed:

```text
python manage.py createadminuser --username admin --email admin@example.com --password secret --no-input
```

### `startadmin`

Copies the React admin source into the project so it can be themed and
extended. See [admin-customization.md](https://github.com/0xdps/fast-frame/blob/trunk/docs/admin-customization.md).

```text
python manage.py startadmin              # creates ./admin-ui
python manage.py startadmin ui --force   # replace an existing directory
```

### `buildadmin`

Runs `npm run build` and copies the compiled files. By default the source is
the admin template inside FastFrame and the output is `fastframe/admin/static`
(the bundle served when `ADMIN_MODE = "static"`).

```text
python manage.py buildadmin
python manage.py buildadmin --source admin-ui --output admin-ui/dist
```

## App commands

An installed app adds a `manage.py` command by shipping a module. The file name is the command name:

```text
users/management/commands/greet.py
```

```python
def add_arguments(parser) -> None:
    parser.add_argument("name")


def execute(args) -> None:
    print(f"hello {args.name}")
```

`python manage.py greet ada` calls `execute`. `add_arguments` is optional. The module docstring's first line is the help text.

FastFrame loads these modules from each entry in `INSTALLED_APPS`. An app that is not installed contributes nothing. A missing `management/commands` package is normal. A command module must define `execute(args)`.

A command name that matches a built-in command, or the same name from two installed apps, is an error. Built-in commands stay the ones that ship with FastFrame.

## Future

- `check --deploy`
- `collectstatic` when static files exist
