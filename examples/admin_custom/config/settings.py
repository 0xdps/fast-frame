"""Advanced admin: a React project in this repo, built and served by FastAPI."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/admin_custom.db")

DEFAULT_AUTO_FIELD = "AutoField"
AUTH_USER_MODEL = "auth.User"

ADMIN_MODE = "custom"
ADMIN_SITE_TITLE = "Custom Admin"

APP_NAME = "Custom Admin API"

INSTALLED_APPS = [
    "fastframe.contrib.auth",  # admin login uses the default User model
    "fastframe.admin",
    "fastframe.docs",
]
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True
