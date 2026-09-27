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
ENABLE_ADMIN_DOCS = True
ADMIN_MODE = "static"

# Apps — admin + general auth API on by default here, matching the old
# ENABLE_ADMIN=True/ENABLE_AUTH_API=True defaults this fixture relied on.
INSTALLED_APPS = [
    "fastframe.contrib.auth",  # default user model + general /api/auth/*
    "fastframe.admin",
    "fastframe.docs",
]

# Secret key for tests
SECRET_KEY = "test-secret-key-not-for-production"
DEBUG = True