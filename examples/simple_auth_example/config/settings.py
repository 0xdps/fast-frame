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
# This example wires admin manually in app.py (app.include_router(...)),
# not via get_asgi_application()/create_app(), so admin isn't gated by
# INSTALLED_APPS here — see app.py's "Admin setup" section.
ADMIN_MODE = "static"  # Use pre-built static admin
ADMIN_SITE_TITLE = "Auth Example Admin"
ADMIN_SITE_HEADER = "User Management"

# Apps
INSTALLED_APPS = [
    "fastframe.contrib.auth",  # Built-in User model, for makemigrations/migrate
]

# Secret key (change in production!)
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True