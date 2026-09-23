"""Blog application settings."""

import os
from pathlib import Path

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/blog.db")

# Apps
INSTALLED_APPS = [
    "users",
    "posts",
    "comments",
]

# Middleware (for future)
MIDDLEWARE = []

# Secret key (change in production!)
SECRET_KEY = "dev-secret-key-change-in-production"

# Debug
DEBUG = True
