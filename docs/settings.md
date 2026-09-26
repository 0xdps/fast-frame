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
it. See [ADMIN_SECURITY_WARNING.md](ADMIN_SECURITY_WARNING.md). Per-model
permission enforcement (`ModelAdmin.enforce_permissions`) is opt-in — see
[permissions.md](permissions.md).

## REST API

Opt-in, token-authenticated CRUD over the same models registered with
`admin_site` — see [rest-api.md](rest-api.md).

| Setting | Default | Meaning |
| --- | --- | --- |
| `ENABLE_REST_API` | `False` | Mount `/api/auth/token` and the CRUD API. Off by default, unlike admin. |
| `ENABLE_REST_API_DOCS` | `True` | Include REST API operations in the OpenAPI schema. |
| `API_PREFIX` | `"/api/v1"` | CRUD API prefix (token auth lives at `/api/auth/token` regardless). |
| `API_TOKEN_DEFAULT_EXPIRY_DAYS` | `None` | Default lifetime for new tokens, in days. `None` = tokens never expire unless `expires_in_days` (or the `expiresInDays` field on `POST /api/auth/token`) is passed explicitly. |

## General-purpose auth API

Session-cookie login for any app route, independent of `can_access_admin`
— shares the same cookie as the admin. See
[auth.md](auth.md#general-purpose-session-auth-outside-admin).

| Setting | Default | Meaning |
| --- | --- | --- |
| `ENABLE_AUTH_API` | `True` | Mount `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`. |
| `PASSWORD_MIN_LENGTH` | `8` | Minimum length enforced by `User.set_password()` (skip with `validate=False`). |

## Rate limiting

In-memory, single-process sliding-window limiter applied to
`/api/admin/login`, `/api/auth/login`, and `/api/auth/token`. Not shared
across processes/instances — meant to blunt naive brute-forcing, not as a
distributed production rate limiter (front a multi-instance deployment
with a real backend, e.g. Redis, behind a load balancer, for that).

| Setting | Default | Meaning |
| --- | --- | --- |
| `RATE_LIMIT_LOGIN_ENABLED` | `True` | Set `False` to disable entirely. |
| `RATE_LIMIT_LOGIN_MAX_ATTEMPTS` | `5` | Failed attempts allowed per window before lockout. |
| `RATE_LIMIT_LOGIN_WINDOW_SECONDS` | `60` | Sliding window length. |
| `RATE_LIMIT_LOGIN_LOCKOUT_SECONDS` | `300` | How long a bucket stays locked out after hitting the max. |

Locked-out requests get `429` with a `Retry-After` header. A successful
login resets the counter for that identifier (username + client IP).

## CORS and security headers

| Setting | Default | Meaning |
| --- | --- | --- |
| `CORS_ALLOWED_ORIGINS` | `[]` | Empty = CORS disabled entirely (no headers added). Non-empty enables Starlette's `CORSMiddleware` with these origins. |
| `CORS_ALLOW_CREDENTIALS` | `False` | Passed through to `CORSMiddleware`. |
| `CORS_ALLOW_METHODS` | `["*"]` | Passed through to `CORSMiddleware`. |
| `CORS_ALLOW_HEADERS` | `["*"]` | Passed through to `CORSMiddleware`. |
| `SECURE_HEADERS` | `True` | Adds `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` on every response; adds `Strict-Transport-Security` too, but only when `DEBUG = False`. |
| `MIDDLEWARE` | `[]` | Dotted paths (`"module.ClassName"`) to your own Starlette-compatible middleware, applied in list order. Added before the built-in CORS/security-headers middleware, so those two end up wrapping your custom middleware (CORS outermost). |

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
