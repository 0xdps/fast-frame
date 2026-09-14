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
