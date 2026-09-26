"""Test settings for FastFrame tests."""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Database - will be overridden by individual tests
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///test.db")

# Use default auth user model for most tests
AUTH_USER_MODEL = "auth.User"

# Use AutoField by default (faster for tests)
DEFAULT_AUTO_FIELD = "AutoField"

# Admin settings
ENABLE_ADMIN = True
ENABLE_ADMIN_DOCS = True
ADMIN_MODE = "static"
# This settings module covers general app-wiring tests, not admin auth —
# see test_admin_auth.py for login/logout/session coverage.
ADMIN_REQUIRE_AUTH = False

# Apps
INSTALLED_APPS = [
    "auth",  # For the default user model
]

# Secret key for tests
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True