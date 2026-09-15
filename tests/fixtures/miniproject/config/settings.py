"""Minimal FastFrame settings for integration tests."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = "MiniProject"
DEBUG = True

INSTALLED_APPS = [
    "health",
    "users",
    "posts",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")

SHELL_AUTO_IMPORT_MODELS = True
SHELL_IMPORTS = [
    "from fastframe.db.session import session_scope",
]
SHELL_STARTUP = "config/shell_startup.py"
