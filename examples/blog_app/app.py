#!/usr/bin/env python
"""
FastAPI app with Admin interface for the blog demo.

Run with:
    uvicorn app:app --reload

Then visit:
    http://localhost:8000/admin/
"""

import hashlib
import os
import secrets
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import validates

from fastframe.admin import ModelAdmin, admin_site, get_admin_api_router, get_admin_router
from fastframe.core.bootstrap import bootstrap
from fastframe.models import Model, ValidationError, fields

# Initialize FastFrame
bootstrap()

def hash_password(password: str) -> str:
    """Hash a password with PBKDF2. Already-hashed values are returned unchanged."""
    if password.startswith("pbkdf2_sha256$"):
        return password
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


# Define models
class SimpleUser(Model):
    """Account used by the admin. Password is stored hashed and never returned by the API."""

    id = fields.UUIDField(primary_key=True)
    first_name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.EmailField(unique=True)
    password = fields.CharField(max_length=255, write_only=True)
    is_active = fields.BooleanField(default=True)
    preferences = fields.JSONField(default=dict)

    class Meta:
        db_table = "simple_users"
        ordering = ["username"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        app_label = "users"

    @validates("password")
    def _hash_password(self, _key: str, value: str | None) -> str | None:
        if not value:
            return value
        return hash_password(value)

    def clean(self):
        if not self.username.replace("_", "").isalnum():
            raise ValidationError("Username must be alphanumeric")


class Category(Model):
    """Blog category."""
    
    name = fields.CharField(max_length=100, unique=True)
    slug = fields.CharField(max_length=100, unique=True)
    description = fields.TextField(blank=True, default="")
    post_count = fields.IntegerField(default=0)
    
    class Meta:
        db_table = "categories"
        ordering = ["name"]
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        app_label = "blog"


class Post(Model):
    """Blog post."""
    
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True)
    content = fields.TextField()
    summary = fields.CharField(max_length=500, blank=True, default="")
    
    status = fields.CharField(
        max_length=20,
        default="draft",
        choices=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ]
    )
    
    is_featured = fields.BooleanField(default=False)
    view_count = fields.IntegerField(default=0)
    like_count = fields.IntegerField(default=0)
    
    class Meta:
        db_table = "posts"
        ordering = ["-id"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        app_label = "blog"


class Tag(Model):
    """Content tag."""
    
    name = fields.CharField(max_length=50, unique=True)
    slug = fields.CharField(max_length=50, unique=True)
    usage_count = fields.IntegerField(default=0)
    
    class Meta:
        db_table = "tags"
        ordering = ["name"]
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
        app_label = "blog"


class Comment(Model):
    """Comment on a post."""
    
    author_name = fields.CharField(max_length=100)
    author_email = fields.EmailField()
    content = fields.TextField()
    is_approved = fields.BooleanField(default=False)
    like_count = fields.IntegerField(default=0)
    
    class Meta:
        db_table = "comments"
        ordering = ["-id"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        app_label = "blog"


# Configure admin classes
class SimpleUserAdmin(ModelAdmin):
    list_display = ["first_name", "last_name", "username", "email", "is_active"]
    search_fields = ["first_name", "last_name", "username", "email"]
    list_filter = ["is_active"]
    list_per_page = 50


class CategoryAdmin(ModelAdmin):
    list_display = ["name", "slug", "post_count"]
    search_fields = ["name", "description"]
    list_per_page = 50


class PostAdmin(ModelAdmin):
    list_display = ["title", "status", "is_featured", "view_count", "like_count"]
    search_fields = ["title", "content", "summary"]
    list_filter = ["status", "is_featured"]
    list_per_page = 25


class TagAdmin(ModelAdmin):
    list_display = ["name", "slug", "usage_count"]
    search_fields = ["name"]
    list_per_page = 50


class CommentAdmin(ModelAdmin):
    list_display = ["author_name", "author_email", "is_approved", "like_count"]
    search_fields = ["author_name", "author_email", "content"]
    list_filter = ["is_approved"]
    list_per_page = 50


# Register all models with admin
admin_site.register(SimpleUser, SimpleUserAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Post, PostAdmin)
admin_site.register(Tag, TagAdmin)
admin_site.register(Comment, CommentAdmin)


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


# Include admin routers: SSR views (legacy) + REST API (for React admin)
app.include_router(get_admin_router())
app.include_router(get_admin_api_router())


# Sample API endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to Blog App",
        "admin": "/admin/",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
