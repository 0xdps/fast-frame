"""Settings with admin disabled (i.e. not installed)."""

# Database
DATABASE_URL = "sqlite:///./test_no_admin.db"

# Apps — admin is "disabled" simply by not being listed here.
# Docs stay on so this fixture still has a schema if a test asks for one.
INSTALLED_APPS = [
    "fastframe.docs",
]
