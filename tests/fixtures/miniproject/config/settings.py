"""Minimal FastFrame settings for integration tests."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

APP_NAME = "MiniProject"
DEBUG = True

INSTALLED_APPS = [
    "health",
    "users",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
