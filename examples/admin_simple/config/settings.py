"""Simple admin: compiled UI served by the same process as the API."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/admin_simple.db")

DEFAULT_AUTO_FIELD = "UUIDField"
AUTH_USER_MODEL = "auth.User"

ENABLE_ADMIN = True
ADMIN_MODE = "static"
ADMIN_SITE_TITLE = "Simple Admin"

ENABLE_OPENAPI = True
OPENAPI_TITLE = "Simple Admin API"

INSTALLED_APPS = []
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True
