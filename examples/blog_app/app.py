#!/usr/bin/env python
"""
FastAPI app with Admin interface for the blog demo.

Run with:
    uvicorn app:app --reload

Then visit:
    http://localhost:8000/admin/       (SSR admin, optional)
    http://localhost:8000/api/admin/   (REST API for React admin)
    http://localhost:8000/             (Serves React admin if built, optional)
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from fastframe.admin import get_admin_api_router
from fastframe.core.bootstrap import bootstrap
from fastframe.models import Model

# Initialize FastFrame
bootstrap()

# Import models and admin classes to register them
from blog import admin as blog_admin  # noqa: F401, E402
from blog import models as blog_models  # noqa: F401, E402
from users import admin as users_admin  # noqa: F401, E402
from users import models as users_models  # noqa: F401, E402

# Create FastAPI app
app = FastAPI(
    title="Blog App with Admin",
    description="FastFrame Admin Demo",
    version="0.3.0",
)

# CORS for the React admin dev server (Vite on :5173)
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
# Admin setup (all optional)
# ------------------------------------------------------------------

# Option 1: Include SSR admin at /admin/ (legacy, optional)
# app.include_router(get_admin_router())

# Option 2: Include REST API at /api/admin/ for React admin
app.include_router(get_admin_api_router())

# Option 3: Serve built React admin from /admin-ui/ (optional)
# Build the admin-ui first: cd admin-ui && npm run build
# Then uncomment:
# admin_ui_dist = Path(__file__).parent / "admin-ui" / "dist"
# if admin_ui_dist.exists():
#     app.mount("/admin-ui", StaticFiles(directory=admin_ui_dist, html=True), name="admin")

# ------------------------------------------------------------------
# Application routes
# ------------------------------------------------------------------


@app.get("/")
async def root():
    return {
        "message": "Welcome to Blog App",
        "admin_api": "/api/admin/",
        "admin_ui_dev": "http://localhost:5173 (run: cd admin-ui && npm run dev)",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
