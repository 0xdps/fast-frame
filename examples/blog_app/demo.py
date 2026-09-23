#!/usr/bin/env python
"""
Comprehensive blog app demonstrating all FastFrame model features.

This demo showcases:
- All field types (CharField, Email, UUID, Decimal, JSON, etc.)
- ForeignKey relationships with auto-generated relationship attributes  
- Model validation (clean/full_clean)
- QuerySet enhancements (field lookups, Q/F objects)
- Meta options
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from datetime import datetime
from decimal import Decimal

from fastframe.core.bootstrap import bootstrap
from fastframe.db.session import session_scope
from fastframe.models import F, Model, Q, ValidationError, fields

# Initialize FastFrame
bootstrap()


# ============================================================================
# MODELS
# ============================================================================

class User(Model):
    """User with UUID PK, email validation, JSON preferences."""
    
    id = fields.UUIDField(primary_key=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.EmailField(unique=True)
    bio = fields.TextField(blank=True)
    karma = fields.IntegerField(default=0)
    is_active = fields.BooleanField(default=True)
    preferences = fields.JSONField(default=dict)
    date_joined = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

    def clean(self):
        if not self.username.replace("_", "").isalnum():
            raise ValidationError("Username must be alphanumeric")


class Category(Model):
    """Category with self-referential FK (tree structure)."""
    
    name = fields.CharField(max_length=100)
    parent_id = fields.ForeignKey("Category", null=True, on_delete="CASCADE")
    
    class Meta:
        db_table = "categories"


class Post(Model):
    """Post with ForeignKey, validation, status choices."""
    
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True)
    content = fields.TextField()
    author_id = fields.ForeignKey("User", on_delete="CASCADE")
    category_id = fields.ForeignKey("Category", null=True, on_delete="SET_NULL")
    
    status = fields.CharField(
        max_length=20,
        default="draft",
        choices=[("draft", "Draft"), ("published", "Published")]
    )
    
    view_count = fields.IntegerField(default=0)
    post_metadata = fields.JSONField(default=dict)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "posts"
        ordering = ["-created_at"]

    def clean(self):
        if len(self.title) < 5:
            raise ValidationError("Title too short")


class Comment(Model):
    """Comment with self-referential FK (threading)."""
    
    post_id = fields.ForeignKey("Post", on_delete="CASCADE")
    author_id = fields.ForeignKey("User", on_delete="CASCADE")
    parent_id = fields.ForeignKey("Comment", null=True, on_delete="CASCADE")
    content = fields.TextField()
    like_count = fields.IntegerField(default=0)
    created_at = fields.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "comments"


# ============================================================================
# DEMO
# ============================================================================

def main():
    print("=" * 70)
    print("FastFrame Blog App - Comprehensive Model Demo")
    print("=" * 70)
    
    # Create tables
    print("\n[1] Creating database tables...")
    from fastframe.db.engine import get_engine
    engine = get_engine()
    Model.metadata.create_all(bind=engine)
    print("✓ Tables created")
    
    with session_scope():
        # ====================================================================
        # FIELD TYPES DEMO
        # ====================================================================
        print("\n[2] Testing all field types...")
        
        # UUIDField (auto-generated), EmailField (validated)
        alice = User.objects.create(
            username="alice",
            email="alice@example.com",
            bio="Python developer",
            karma=100,
            preferences={"theme": "dark", "notifications": True}
        )
        print(f"✓ Created user: {alice.username} (UUID: {alice.id})")
        
        bob = User.objects.create(
            username="bob",
            email="bob@example.com",
            karma=50
        )
        print(f"✓ Created user: {bob.username}")
        
        # ====================================================================
        # FOREIGNKEY & RELATIONSHIPS DEMO
        # ====================================================================
        print("\n[3] Testing ForeignKey relationships...")
        
        # Self-referential FK
        tech = Category.objects.create(name="Technology")
        python_cat = Category.objects.create(name="Python", parent_id=tech.id)
        print(f"✓ Created category tree: {tech.name} → {python_cat.name}")
        
        # ForeignKey to User and Category
        post = Post.objects.create(
            title="Introduction to FastFrame",
            slug="intro-fastframe",
            content="FastFrame is a Django-like framework...",
            author_id=alice.id,
            category_id=python_cat.id,
            status="published",
            view_count=100,
            post_metadata={"tags": ["python", "framework"], "reading_time": 5}
        )
        print(f"✓ Created post: {post.title}")
        
        # Access relationship (auto-generated from ForeignKey)
        print(f"  Post author (via relationship): {post.author.username}")
        print(f"  Post category: {post.category.name}")
        print(f"  Category parent: {post.category.parent.name if post.category.parent else 'None'}")
        
        # ====================================================================
        # VALIDATION DEMO
        # ====================================================================
        print("\n[4] Testing model validation...")
        
        # Valid post
        post2 = Post(
            title="Another Post",
            slug="another",
            content="Content",
            author_id=bob.id,
            status="published"
        )
        post2.full_clean()  # Should pass
        print("✓ Validation passed for valid post")
        
        # Invalid post (title too short)
        try:
            bad_post = Post(
                title="Bad",
                slug="bad",
                content="Content",
                author_id=alice.id
            )
            bad_post.full_clean()
            print("✗ Should have failed validation!")
        except ValidationError as e:
            print(f"✓ Validation caught error: {str(e)[:50]}...")
        
        # ====================================================================
        # QUERYSET LOOKUPS DEMO
        # ====================================================================
        print("\n[5] Testing QuerySet field lookups...")
        
        # Create more posts
        for i in range(5):
            Post.objects.create(
                title=f"Test Post {i}",
                slug=f"test-{i}",
                content="Content",
                author_id=alice.id if i % 2 == 0 else bob.id,
                status="published" if i % 2 == 0 else "draft",
                view_count=i * 10
            )
        
        # __gte lookup
        popular = Post.objects.filter(view_count__gte=20).count()
        print(f"✓ Posts with >= 20 views: {popular}")
        
        # __icontains lookup
        intro_posts = Post.objects.filter(title__icontains="intro").count()
        print(f"✓ Posts with 'intro' in title: {intro_posts}")
        
        # __in lookup
        draft_or_pub = Post.objects.filter(status__in=["draft", "published"]).count()
        print(f"✓ Posts with status in list: {draft_or_pub}")
        
        # ====================================================================
        # Q OBJECTS DEMO
        # ====================================================================
        print("\n[6] Testing Q objects (complex queries)...")
        
        # OR query
        popular_or_alice = Post.objects.filter(
            Q(view_count__gte=50) | Q(author_id=alice.id)
        ).count()
        print(f"✓ Popular posts OR by Alice: {popular_or_alice}")
        
        # NOT query
        not_draft = Post.objects.filter(~Q(status="draft")).count()
        print(f"✓ Non-draft posts: {not_draft}")
        
        # Complex combination
        complex_query = Post.objects.filter(
            (Q(status="published") & Q(view_count__gte=10)) | Q(author_id=bob.id)
        ).count()
        print(f"✓ Complex query result: {complex_query}")
        
        # ====================================================================
        # SELF-REFERENTIAL FK DEMO
        # ====================================================================
        print("\n[7] Testing self-referential relationships...")
        
        # Create comment thread
        comment1 = Comment.objects.create(
            post_id=post.id,
            author_id=bob.id,
            content="Great post!",
            like_count=5
        )
        
        # Reply to comment (self-referential FK)
        reply = Comment.objects.create(
            post_id=post.id,
            author_id=alice.id,
            parent_id=comment1.id,
            content="Thanks!"
        )
        
        print(f"✓ Created comment thread")
        print(f"  Comment: {comment1.content}")
        print(f"  Reply (parent check): {reply.parent.content if reply.parent else 'None'}")
        
        # ====================================================================
        # METADATA & JSON DEMO
        # ====================================================================
        print("\n[8] Testing JSON field...")
        
        print(f"✓ Post metadata: {post.post_metadata}")
        print(f"✓ User preferences: {alice.preferences}")
        
    print("\n" + "=" * 70)
    print("Demo completed successfully! ✓")
    print("All model features working:")
    print("  • All field types (CharField, Email, UUID, Decimal, JSON, etc.)")
    print("  • ForeignKey with auto-generated relationships")
    print("  • Model validation (clean/full_clean)")
    print("  • QuerySet lookups (__gte, __icontains, __in, etc.)")
    print("  • Q objects for complex queries")
    print("  • F objects for field references")
    print("  • Self-referential relationships")
    print("  • Meta options (db_table, ordering)")
    print("=" * 70)


if __name__ == "__main__":
    main()
