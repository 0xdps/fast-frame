# Settings

Project settings are a Python module named by `FASTFRAME_SETTINGS_MODULE`
(default in generated projects: `config.settings`). Uppercase names override
`fastframe.conf.global_settings`.

Read them with:

```python
from fastframe.conf import settings

settings.ENABLE_ADMIN
```

`bootstrap()` and `create_app()` reload this object after the environment
variable is set.

## Admin

| Setting | Default | Meaning |
| --- | --- | --- |
| `ENABLE_ADMIN` | `True` | Mount the admin UI and API. `False` omits both, including from OpenAPI. |
| `ENABLE_ADMIN_DOCS` | `True` | Include admin API operations in the OpenAPI schema. |
| `ADMIN_MODE` | `"static"` | `"static"` serves the compiled React UI shipped with FastFrame. `"custom"` serves `admin-ui/dist` (built via `manage.py startadmin`). The admin UI is React-only — there is no server-rendered mode. |
| `ADMIN_PREFIX` | `"/admin"` | UI URL prefix. |
| `ADMIN_API_PREFIX` | `"/api/admin"` | REST API prefix. |
| `ADMIN_SITE_TITLE` | `"FastFrame Admin"` | Title used by project code and docs. |
| `ADMIN_SITE_HEADER` | `"Administration"` | Header label. |

Admin authentication is always required — there is no setting to disable
it. See [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md).

## REST API

Opt-in, token-authenticated CRUD over the same models registered with
`admin_site` — see [rest-api.md](rest-api.md).

| Setting | Default | Meaning |
| --- | --- | --- |
| `ENABLE_REST_API` | `False` | Mount `/api/auth/token` and the CRUD API. Off by default, unlike admin. |
| `ENABLE_REST_API_DOCS` | `True` | Include REST API operations in the OpenAPI schema. |
| `API_PREFIX` | `"/api/v1"` | CRUD API prefix (token auth lives at `/api/auth/token` regardless). |

## OpenAPI

| Setting | Default | Meaning |
| --- | --- | --- |
| `ENABLE_OPENAPI` | `True` | `False` disables the schema, Swagger UI, and ReDoc. |
| `OPENAPI_URL` | `"/openapi.json"` | Schema path. |
| `SWAGGER_UI_URL` | `"/docs"` | Swagger UI. Set `None` to disable only Swagger. |
| `REDOC_URL` | `"/redoc"` | ReDoc. Set `None` to disable only ReDoc. |
| `OPENAPI_TITLE` | `"FastFrame API"` | Schema title. |
| `OPENAPI_VERSION` | `"1.0.0"` | Schema version. |
| `OPENAPI_DESCRIPTION` | `"API Documentation"` | Schema description. |

`create_app()` applies these. Keyword arguments passed to `create_app()`
override them.

## Auth and primary keys

| Setting | Default |
| --- | --- |
| `AUTH_USER_MODEL` | `"auth.User"` |
| `DEFAULT_AUTO_FIELD` | `"AutoField"` |
| `UUID_GENERATION` | `"python"` |

Details: [auth.md](auth.md).

## Database and apps

| Setting | Default |
| --- | --- |
| `DATABASE_URL` | `"sqlite:///./db.sqlite3"` |
| `INSTALLED_APPS` | `[]` |
| `SECRET_KEY` | development placeholder |
| `DEBUG` | `True` |
