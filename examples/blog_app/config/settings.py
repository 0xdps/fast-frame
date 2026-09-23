"""Blog application settings."""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/blog.db")

# ===== Primary Keys =====
DEFAULT_AUTO_FIELD = "UUIDField"  # Use UUID v7 for better performance

# ===== Auth =====
# Use custom user model instead of default auth.User
AUTH_USER_MODEL = "users.SimpleUser"

# ===== Admin =====
ENABLE_ADMIN = True
ADMIN_MODE = "static"  # Use pre-built admin, change to "custom" for React admin
ADMIN_SITE_TITLE = "Blog Admin"
ADMIN_SITE_HEADER = "Blog Administration"

# ===== OpenAPI =====
OPENAPI_TITLE = "Blog API"
OPENAPI_DESCRIPTION = "FastFrame Blog Demo API"

# Apps
INSTALLED_APPS = [
    "users",
    "blog",
]

# Middleware (for future)
MIDDLEWARE = []

# Secret key (change in production!)
SECRET_KEY = "dev-secret-key-change-in-production"

# Debug
DEBUG = True
