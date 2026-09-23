"""Custom user model example."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/custom_user.db")

DEFAULT_AUTO_FIELD = "AutoField"
AUTH_USER_MODEL = "accounts.CustomUser"

ENABLE_ADMIN = True
ADMIN_MODE = "static"

INSTALLED_APPS = ["accounts"]
SECRET_KEY = "dev-secret-key-change-in-production"
DEBUG = True
