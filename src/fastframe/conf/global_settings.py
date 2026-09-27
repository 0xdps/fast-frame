"""
Global settings for FastFrame.

These are the defaults that can be overridden in a user's settings.py file.
"""

# ===== Primary Keys =====
DEFAULT_AUTO_FIELD = "AutoField"  # "AutoField" | "BigAutoField" | "UUIDField"

# ===== UUID Configuration =====
# Always use UUID v7 (time-ordered, database-optimized)
UUID_GENERATION = "python"  # "python" | "database"

# ===== Auth =====
AUTH_USER_MODEL = "auth.User"  # Default user model, can be overridden

# ===== Admin =====
# Whether the admin is mounted at all is controlled by ``INSTALLED_APPS``
# (add ``"fastframe.admin"``) — not a setting here. See docs/admin-setup.md.
ENABLE_ADMIN_DOCS = True  # Include admin endpoints in OpenAPI schema
ADMIN_SITE_TITLE = "FastFrame Admin"
ADMIN_SITE_HEADER = "Administration"
ADMIN_PREFIX = "/admin"
ADMIN_API_PREFIX = "/api/admin"
ADMIN_MODE = "static"  # "static" (pre-built) or "custom" (user builds)
# Admin always requires a logged-in User with can_access_admin — there is
# no setting to disable this (see docs/ADMIN_SECURITY_WARNING.md).

# ===== REST API (generic, token-authenticated CRUD) =====
# Whether this is mounted at all is controlled by ``INSTALLED_APPS`` (add
# ``"fastframe.api"``) — not a setting here. See docs/rest-api.md.
ENABLE_REST_API_DOCS = True  # Include REST API endpoints in OpenAPI schema
API_PREFIX = "/api/v1"

# ===== API tokens =====
# Default lifetime for new tokens, in days. None = tokens never expire
# unless expires_in_days is passed explicitly to create_token()/POST /api/auth/token.
API_TOKEN_DEFAULT_EXPIRY_DAYS: int | None = None

# ===== General-purpose session auth (outside /admin) =====
# POST/DELETE /api/auth/login, /api/auth/logout, GET /api/auth/me — a
# plain login for any active user, independent of can_access_admin. Uses
# the same signed session cookie mechanism as the admin. Mounted when
# ``"fastframe.contrib.auth"`` is in ``INSTALLED_APPS`` — not a setting
# here. See docs/auth.md.

# ===== Password policy =====
PASSWORD_MIN_LENGTH = 8

# ===== Rate limiting (in-memory, single-process) =====
# Applied to /api/admin/login, /api/auth/login, and /api/auth/token.
# Not shared across processes/instances — use a real backend (e.g. Redis)
# behind a load balancer; this is meant to blunt naive brute-forcing.
RATE_LIMIT_LOGIN_ENABLED = True
RATE_LIMIT_LOGIN_MAX_ATTEMPTS = 5
RATE_LIMIT_LOGIN_WINDOW_SECONDS = 60
RATE_LIMIT_LOGIN_LOCKOUT_SECONDS = 300

# ===== CORS =====
# Empty list = CORS disabled (no CORS headers added at all).
CORS_ALLOWED_ORIGINS: list[str] = []
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_METHODS: list[str] = ["*"]
CORS_ALLOW_HEADERS: list[str] = ["*"]

# ===== Security headers =====
# Adds X-Content-Type-Options, X-Frame-Options, Referrer-Policy on every
# response; adds Strict-Transport-Security too, but only when DEBUG=False.
SECURE_HEADERS = True

# ===== OpenAPI/Swagger =====
# Whether /docs, /redoc, and /openapi.json exist is controlled by
# ``INSTALLED_APPS`` (add ``"fastframe.docs"``) — not a setting here.
# FastAPI still serves them. FastFrame does not ship a second docs UI.

# ===== Database =====
DATABASE_URL = "sqlite:///./db.sqlite3"

# ===== Apps =====
INSTALLED_APPS = []

# ===== Middleware =====
# Dotted paths to Starlette-compatible middleware classes (each must accept
# just `app` in its constructor and read any settings it needs itself),
# applied in list order via app.add_middleware(). Applied *after* the
# built-in CORS/security-headers middleware (see CORS_ALLOWED_ORIGINS,
# SECURE_HEADERS above), which are independent of this list.
MIDDLEWARE: list[str] = []

# ===== Security =====
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True