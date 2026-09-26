"""Settings for admin authentication integration tests."""

# Database
DATABASE_URL = "sqlite:///./test_admin_auth.db"

# Auth
AUTH_USER_MODEL = "auth.User"
DEFAULT_AUTO_FIELD = "AutoField"

# Admin — auth is always required (no setting to disable it)
ENABLE_ADMIN_DOCS = True
ADMIN_MODE = "static"
ADMIN_SITE_TITLE = "Test Admin"
ADMIN_PREFIX = "/admin"
ADMIN_API_PREFIX = "/api/admin"

# OpenAPI
ENABLE_OPENAPI = True
SWAGGER_UI_URL = "/docs"

# Apps
INSTALLED_APPS = [
    "fastframe.contrib.auth",
    "fastframe.admin",
]

# Security
SECRET_KEY = "test-secret-key-for-admin-auth-tests"
