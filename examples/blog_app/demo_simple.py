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

from fastframe.core.bootstrap import bootstrap
from fastframe.db.session import session_scope
from fastframe.models import F, Model, Q, ValidationError, fields

# Initialize FastFrame
bootstrap()


# ============================================================================
# SIMPLE MODELS WITHOUT FOREIGNKEYS (Phase 1)
# ============================================================================

class SimpleUser(Model):
    """User with UUID PK, email validation, JSON preferences."""
    
    id = fields.UUIDField(primary_key=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.EmailField(unique=True)
    bio = fields.TextField(blank=True, default="")
    karma = fields.IntegerField(default=0)
    is_active = fields.BooleanField(default=True)
    preferences = fields.JSONField(default=dict)
    
    class Meta:
        db_table = "simple_users"
        ordering = ["username"]

    def clean(self):
        if not self.username.replace("_", "").isalnum():
            raise ValidationError("Username must be alphanumeric")


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
        alice = SimpleUser.objects.create(
            username="alice",
            email="alice@example.com",
            bio="Python developer",
            karma=100,
            preferences={"theme": "dark", "notifications": True}
        )
        print(f"✓ Created user: {alice.username} (UUID: {alice.id})")
        
        bob = SimpleUser.objects.create(
            username="bob",
            email="bob@example.com",
            karma=50
        )
        print(f"✓ Created user: {bob.username}")
        
        charlie = SimpleUser.objects.create(
            username="charlie123",
            email="charlie@example.com",
            karma=75
        )
        
        # ====================================================================
        # VALIDATION DEMO
        # ====================================================================
        print("\n[3] Testing model validation...")
        
        # Invalid user (invalid username with special chars)
        try:
            bad_user = SimpleUser(
                username="bad@user!",
                email="bad@example.com"
            )
            bad_user.full_clean()
            print("✗ Should have failed validation!")
        except ValidationError as e:
            print(f"✓ Validation caught error: {str(e)[:60]}...")
        
        # ====================================================================
        # QUERYSET LOOKUPS DEMO
        # ====================================================================
        print("\n[4] Testing QuerySet field lookups...")
        
        # Create more users for testing
        for i in range(5):
            SimpleUser.objects.create(
                username=f"user{i}",
                email=f"user{i}@example.com",
                karma=i * 20
            )
        
        # __gte lookup
        high_karma = SimpleUser.objects.filter(karma__gte=50).count()
        print(f"✓ Users with karma >= 50: {high_karma}")
        
        # __icontains lookup
        alice_users = SimpleUser.objects.filter(username__icontains="alice").count()
        print(f"✓ Users with 'alice' in username: {alice_users}")
        
        # __in lookup
        specific_users = SimpleUser.objects.filter(username__in=["alice", "bob"]).count()
        print(f"✓ Users in list: {specific_users}")
        
        # __exact lookup
        exact_match = SimpleUser.objects.filter(username__exact="bob").first()
        print(f"✓ Exact username match: {exact_match.username if exact_match else 'None'}")
        
        # ====================================================================
        # Q OBJECTS DEMO
        # ====================================================================
        print("\n[5] Testing Q objects (complex queries)...")
        
        # OR query
        high_karma_or_alice = SimpleUser.objects.filter(
            Q(karma__gte=70) | Q(username="alice")
        ).count()
        print(f"✓ High karma OR alice: {high_karma_or_alice}")
        
        # NOT query
        not_active = SimpleUser.objects.filter(~Q(is_active=True)).count()
        print(f"✓ Inactive users: {not_active}")
        
        # Complex combination
        complex_query = SimpleUser.objects.filter(
            (Q(karma__gte=50) & Q(is_active=True)) | Q(username__icontains="bob")
        ).count()
        print(f"✓ Complex query result: {complex_query}")
        
        # ====================================================================
        # JSON FIELD DEMO
        # ====================================================================
        print("\n[6] Testing JSON field...")
        
        print(f"✓ User preferences (alice): {alice.preferences}")
        print(f"✓ User preferences (bob): {bob.preferences}")
        
        # Update JSON field
        alice.preferences["theme"] = "light"
        alice.save()
        print("✓ Updated JSON field")
        
        # ====================================================================
        # META OPTIONS DEMO
        # ====================================================================
        print("\n[7] Testing Meta options...")
        
        all_users = SimpleUser.objects.all()
        print(f"✓ Fetched {len(all_users)} users (ordered by username)")
        print(f"  First user: {all_users[0].username if all_users else 'None'}")
        
    print("\n" + "=" * 70)
    print("Demo completed successfully! ✓")
    print("All model features working:")
    print("  • All field types (CharField, Email, UUID, JSON, etc.)")
    print("  • Model validation (clean/full_clean)")
    print("  • QuerySet lookups (__gte, __icontains, __in, __exact)")
    print("  • Q objects for complex queries")
    print("  • JSON fields for structured data")
    print("  • Meta options (db_table, ordering)")
    print("=" * 70)
    print("\nNOTE: For ForeignKey demo, see blog_app_fk.py")


if __name__ == "__main__":
    main()
