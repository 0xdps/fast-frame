"""Settings for admin authentication integration tests."""

# Database
DATABASE_URL = "sqlite:///./test_admin_auth.db"

# Auth
AUTH_USER_MODEL = "auth.User"
DEFAULT_AUTO_FIELD = "AutoField"

# Admin — auth enabled (the secure default)
ENABLE_ADMIN = True
ENABLE_ADMIN_DOCS = True
ADMIN_MODE = "static"
ADMIN_SITE_TITLE = "Test Admin"
ADMIN_PREFIX = "/admin"
ADMIN_API_PREFIX = "/api/admin"
ADMIN_REQUIRE_AUTH = True

# OpenAPI
ENABLE_OPENAPI = True
SWAGGER_UI_URL = "/docs"

# Apps
INSTALLED_APPS = [
    "fastframe.contrib.auth",
]

# Security
SECRET_KEY = "test-secret-key-for-admin-auth-tests"
