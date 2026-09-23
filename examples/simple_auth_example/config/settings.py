"""Simple auth example settings."""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/auth_example.db")

# ===== Primary Keys =====
DEFAULT_AUTO_FIELD = "AutoField"  # Use simple integers for this example

# ===== Auth =====
AUTH_USER_MODEL = "auth.User"  # Use default User model

# ===== Admin =====
ENABLE_ADMIN = True
ADMIN_MODE = "static"  # Use pre-built static admin
ADMIN_SITE_TITLE = "Auth Example Admin"
ADMIN_SITE_HEADER = "User Management"

# Apps
INSTALLED_APPS = [
    "auth",  # Built-in auth app
]

# Secret key (change in production!)
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True