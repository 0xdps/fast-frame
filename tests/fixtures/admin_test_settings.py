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

# OpenAPI
ENABLE_OPENAPI = True
SWAGGER_UI_URL = "/docs"

# Apps
INSTALLED_APPS = [
    "fastframe.contrib.auth",
]
