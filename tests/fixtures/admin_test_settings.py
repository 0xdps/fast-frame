"""Settings for admin integration tests."""

# Database
DATABASE_URL = "sqlite:///./test_admin.db"

# Auth
AUTH_USER_MODEL = "auth.User"
DEFAULT_AUTO_FIELD = "AutoField"

# Admin
ENABLE_ADMIN = True
ENABLE_ADMIN_DOCS = True
ADMIN_MODE = "static"
ADMIN_SITE_TITLE = "Test Admin"
ADMIN_PREFIX = "/admin"
ADMIN_API_PREFIX = "/api/admin"
# These tests cover CRUD behavior, not authentication — see
# test_admin_auth.py for login/logout/session coverage with auth enabled.
ADMIN_REQUIRE_AUTH = False

# OpenAPI
ENABLE_OPENAPI = True
SWAGGER_UI_URL = "/docs"

# Apps
INSTALLED_APPS = [
    "fastframe.contrib.auth",
]
