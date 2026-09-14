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
python manage.py shell
python manage.py test
```

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
