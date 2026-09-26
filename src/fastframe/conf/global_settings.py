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
ENABLE_ADMIN = True
ENABLE_ADMIN_DOCS = True  # Include admin endpoints in OpenAPI schema
ADMIN_SITE_TITLE = "FastFrame Admin"
ADMIN_SITE_HEADER = "Administration"
ADMIN_PREFIX = "/admin"
ADMIN_API_PREFIX = "/api/admin"
ADMIN_MODE = "static"  # "static" (pre-built) or "custom" (user builds)
ADMIN_REQUIRE_AUTH = True  # Require a logged-in User with can_access_admin

# ===== OpenAPI/Swagger =====
ENABLE_OPENAPI = True
OPENAPI_URL = "/openapi.json"
SWAGGER_UI_URL = "/docs"  # None to disable
REDOC_URL = "/redoc"  # None to disable
OPENAPI_TITLE = "FastFrame API"
OPENAPI_VERSION = "1.0.0"
OPENAPI_DESCRIPTION = "API Documentation"

# ===== Database =====
DATABASE_URL = "sqlite:///./db.sqlite3"

# ===== Apps =====
INSTALLED_APPS = []

# ===== Middleware =====
MIDDLEWARE = []

# ===== Security =====
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True