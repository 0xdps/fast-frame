#!/usr/bin/env python
"""
Simple auth example demonstrating FastFrame's default User model and admin.

This example shows:
- Default User model with UUID v7 primary keys
- Built-in admin interface (static mode)
- Creating admin users via CLI
- Two admin deployment options

Run with:
    python manage.py createadminuser
    uvicorn app:app --reload

Then visit:
    http://localhost:8000/admin/       (Static admin)
    http://localhost:8000/api/admin/   (REST API)
    http://localhost:8000/docs         (API documentation)
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastframe.admin import get_admin_api_router, get_admin_router
from fastframe.core.bootstrap import bootstrap
from fastframe.models import Model

# Initialize FastFrame
bootstrap()

# Import auth models and admin to register them
from fastframe.contrib.auth import admin as auth_admin  # noqa: E402, F401
from fastframe.contrib.auth import models as auth_models  # noqa: E402, F401

# Create FastAPI app
app = FastAPI(
    title="FastFrame Auth Example",
    description="Demonstrates default User model and admin interface",
    version="1.0.0",
)

# CORS for React admin dev server (if using advanced admin later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create tables on startup
@app.on_event("startup")
async def startup():
    """Create database tables."""
    from fastframe.db.engine import get_engine

    engine = get_engine()
    Model.metadata.create_all(bind=engine)
    print("✓ Database tables created")


# ------------------------------------------------------------------
# Admin setup - demonstrates two deployment options
# ------------------------------------------------------------------

# Option 1: Static admin at /admin/ (pre-built, zero config)
app.include_router(get_admin_router())

# Option 2: REST API at /api/admin/ for React admin
app.include_router(get_admin_api_router())

# ------------------------------------------------------------------
# Application routes
# ------------------------------------------------------------------


@app.get("/")
async def root():
    return {
        "message": "Welcome to FastFrame Auth Example",
        "features": [
            "Default User model with UUID v7 primary keys",
            "Password hashing with PBKDF2",
            "Flexible metadata for permissions and preferences",
            "Static admin interface (zero setup)",
            "REST API for custom frontends"
        ],
        "endpoints": {
            "static_admin": "/admin/",
            "api": "/api/admin/",
            "docs": "/docs"
        },
        "next_steps": [
            "1. Create admin user: python manage.py createadminuser",
            "2. Visit /admin/ for the static admin interface",
            "3. Or visit /api/admin/ for the REST API",
            "4. Advanced option: python manage.py startadmin"
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)