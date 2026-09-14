"""FastFrame project settings."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = "{{PROJECT_TITLE}}"
DEBUG = os.environ.get("DEBUG", "true").lower() in {"1", "true", "yes"}

INSTALLED_APPS = [
    "health",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{BASE_DIR / 'db.sqlite3'}")

SHELL_AUTO_IMPORT_MODELS = True
# SHELL_IMPORTS = ["from myapp import utils"]
# SHELL_STARTUP = "config/shell_startup.py"  # optional; auto-loads if file exists
