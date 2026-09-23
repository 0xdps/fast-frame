"""Advanced admin: a React project in this repo, built and served by FastAPI."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/admin_custom.db")

DEFAULT_AUTO_FIELD = "AutoField"
AUTH_USER_MODEL = "auth.User"

ENABLE_ADMIN = True
ADMIN_MODE = "custom"
ADMIN_SITE_TITLE = "Custom Admin"

ENABLE_OPENAPI = True
OPENAPI_TITLE = "Custom Admin API"

INSTALLED_APPS = []
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True
