"""Settings with admin disabled (i.e. not installed)."""

# Database
DATABASE_URL = "sqlite:///./test_no_admin.db"

# OpenAPI
ENABLE_OPENAPI = True

# Apps — admin is "disabled" simply by not being listed here.
INSTALLED_APPS = []
