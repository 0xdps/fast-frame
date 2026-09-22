# Todo App (FastFrame example)

A minimal, real end-to-end app built with the actual FastFrame v0.1 developer
loop, used to dogfood the framework and validate the documented workflow.

Generated with:

```bash
fastframe startproject todo_app
cd todo_app
python manage.py startapp todos
```

Then: defined `Todo` model, generated + applied a migration, wrote the
`todos/urls.py` CRUD router by hand (plain FastAPI + Pydantic), and added
tests under `tests/`.

## Run it

```bash
pip install -e /path/to/fast-frame   # installs the fastframe package
python manage.py migrate
python manage.py runserver 8000
python manage.py test -- -v
python manage.py shell               # Todo model is auto-imported
```

## Endpoints

| Method | Path | Description |
| --- | --- | --- |
| GET | `/health` | Built-in health check |
| GET | `/todos` | List todos (optional `?done=true/false`) |
| POST | `/todos` | Create a todo (`{"title": "..."}`) |
| GET | `/todos/{id}` | Get a todo (404 if missing) |
| PATCH | `/todos/{id}` | Update `title` and/or `done` |
| DELETE | `/todos/{id}` | Delete a todo |

## What this validated

- `fastframe startproject` / `manage.py startapp` scaffolding and
  auto-wiring (`INSTALLED_APPS`, router mounting).
- `makemigrations` / `migrate` autogeneration from a plain SQLAlchemy model.
- The manager/QuerySet API (`.create`, `.get`, `.filter`, `.order_by`, `.save`,
  `.delete`) used from plain FastAPI route handlers.
- Automatic `DoesNotExist` → HTTP 404 conversion (no manual `try/except` in
  routes — see `get_todo`).
- `manage.py shell` with model auto-import and the new `Model.__repr__`.
- `manage.py test` via the `client` fixture in `tests/conftest.py`.

See the root [`docs/development.md`](../../docs/development.md) and
[`docs/cli.md`](../../docs/cli.md) for framework-level notes, including two
issues found and fixed while building this example:

- `runserver <port>` (a bare port number) previously bound to the wrong host.
- Test files must obtain the FastAPI `application` via the `client`/
  `project_env` fixtures (inside a fixture/test function), not via a
  module-level `from config.asgi import application` import — otherwise the
  app is built against stale settings and state leaks between tests.
