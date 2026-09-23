#!/usr/bin/env python
"""Populate the database with sample data for testing the admin."""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.core.bootstrap import bootstrap
from fastframe.db.engine import get_engine
from fastframe.db.session import session_scope
from fastframe.models import Model

# Initialize FastFrame
bootstrap()

# Import models from app modules
from blog.models import Category, Comment, Post, Tag
from users.models import SimpleUser


def main():
    print("=" * 70)
    print("Populating Database with Sample Data")
    print("=" * 70)
    
    # Create tables
    print("\n[1] Creating tables...")
    engine = get_engine()
    Model.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    with session_scope():
        # Create users
        print("\n[2] Creating users...")
        users = [
            SimpleUser.objects.create(
                first_name="Alice",
                last_name="Nguyen",
                username="alice",
                email="alice@example.com",
                password="changeme",
                is_active=True,
                preferences={"theme": "dark", "notifications": True},
            ),
            SimpleUser.objects.create(
                first_name="Bob",
                last_name="Martinez",
                username="bob",
                email="bob@example.com",
                password="changeme",
                is_active=True,
                preferences={"theme": "light"},
            ),
            SimpleUser.objects.create(
                first_name="Charlie",
                last_name="Okoye",
                username="charlie",
                email="charlie@example.com",
                password="changeme",
                is_active=True,
                preferences={},
            ),
        ]
        print(f"✓ Created {len(users)} users")
        
        # Create categories
        print("\n[3] Creating categories...")
        categories = [
            Category.objects.create(
                name="Technology",
                slug="technology",
                description="Tech news and tutorials",
                post_count=5
            ),
            Category.objects.create(
                name="Python",
                slug="python",
                description="Python programming",
                post_count=8
            ),
            Category.objects.create(
                name="Web Development",
                slug="web-dev",
                description="Web development tips",
                post_count=12
            ),
        ]
        print(f"✓ Created {len(categories)} categories")
        
        # Create tags
        print("\n[4] Creating tags...")
        tags = [
            Tag.objects.create(name="fastapi", slug="fastapi", usage_count=5),
            Tag.objects.create(name="django", slug="django", usage_count=8),
            Tag.objects.create(name="tutorial", slug="tutorial", usage_count=15),
            Tag.objects.create(name="beginner", slug="beginner", usage_count=10),
            Tag.objects.create(name="advanced", slug="advanced", usage_count=6),
        ]
        print(f"✓ Created {len(tags)} tags")
        
        # Create posts
        print("\n[5] Creating posts...")
        posts = [
            Post.objects.create(
                title="Getting Started with FastAPI",
                slug="getting-started-fastapi",
                content="FastAPI is a modern, fast web framework for building APIs with Python 3.7+...",
                summary="Learn the basics of FastAPI",
                status="published",
                is_featured=True,
                view_count=1250,
                like_count=85
            ),
            Post.objects.create(
                title="Django vs FastAPI: Which to Choose?",
                slug="django-vs-fastapi",
                content="Both Django and FastAPI are excellent Python frameworks...",
                summary="Compare Django and FastAPI",
                status="published",
                is_featured=False,
                view_count=890,
                like_count=45
            ),
            Post.objects.create(
                title="Building RESTful APIs",
                slug="building-restful-apis",
                content="REST API design principles and best practices...",
                summary="API design guide",
                status="published",
                is_featured=True,
                view_count=2100,
                like_count=120
            ),
            Post.objects.create(
                title="Async Python Programming",
                slug="async-python",
                content="Understanding asyncio and async/await in Python...",
                summary="Master async Python",
                status="draft",
                is_featured=False,
                view_count=0,
                like_count=0
            ),
            Post.objects.create(
                title="Database Optimization Tips",
                slug="db-optimization",
                content="How to optimize your database queries...",
                summary="Speed up your database",
                status="published",
                is_featured=False,
                view_count=650,
                like_count=38
            ),
        ]
        print(f"✓ Created {len(posts)} posts")
        
        # Create comments
        print("\n[6] Creating comments...")
        comments = [
            Comment.objects.create(
                author_name="Alice Developer",
                author_email="alice@dev.com",
                content="Great article! Very helpful for beginners.",
                is_approved=True,
                like_count=12
            ),
            Comment.objects.create(
                author_name="Bob Smith",
                author_email="bob@example.com",
                content="Could you elaborate more on the async part?",
                is_approved=True,
                like_count=5
            ),
            Comment.objects.create(
                author_name="Charlie Brown",
                author_email="charlie@test.com",
                content="Thanks for sharing! Looking forward to more.",
                is_approved=True,
                like_count=8
            ),
            Comment.objects.create(
                author_name="Spam Bot",
                author_email="spam@spam.com",
                content="Buy cheap products here!!!",
                is_approved=False,
                like_count=0
            ),
        ]
        print(f"✓ Created {len(comments)} comments")
    
    print("\n" + "=" * 70)
    print("Database populated successfully! ✓")
    print("\nSummary:")
    print(f"  • {len(users)} users")
    print(f"  • {len(categories)} categories")
    print(f"  • {len(tags)} tags")
    print(f"  • {len(posts)} posts")
    print(f"  • {len(comments)} comments")
    print("\nYou can now view them in the admin at http://127.0.0.1:8000/admin/")
    print("=" * 70)


if __name__ == "__main__":
    main()
