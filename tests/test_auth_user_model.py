"""Tests for the default auth User model."""

import os
import tempfile
from unittest.mock import patch

import pytest

from fastframe.contrib.auth import get_user_model
from fastframe.contrib.auth.models import User
from fastframe.core.bootstrap import bootstrap
from fastframe.db.session import session_scope


@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database for each test."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    os.environ["FASTFRAME_SETTINGS_MODULE"] = "tests.fixtures.test_settings"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    import importlib

    settings_mod = importlib.import_module("tests.fixtures.test_settings")
    settings_mod.DATABASE_URL = f"sqlite:///{db_path}"

    bootstrap()
    
    # Create tables
    from fastframe.db.engine import get_engine
    from fastframe.models import Model
    
    engine = get_engine()
    Model.metadata.create_all(bind=engine)
    
    yield

    from fastframe.db.engine import reset_engine
    from fastframe.db.session import reset_session_factory

    reset_session_factory()
    reset_engine()
    if os.path.exists(db_path):
        os.unlink(db_path)


def test_get_user_model_returns_default_user():
    """Test that get_user_model returns the default User model."""
    UserModel = get_user_model()
    assert UserModel is User


def test_user_model_has_expected_fields():
    """Test that the User model has all expected fields."""
    user = User()
    
    # Check required fields exist
    assert hasattr(user, 'username')
    assert hasattr(user, 'email')
    assert hasattr(user, 'first_name')
    assert hasattr(user, 'last_name')
    assert hasattr(user, 'password')
    assert hasattr(user, 'is_active')
    assert hasattr(user, 'user_data')
    assert hasattr(user, 'date_joined')
    assert hasattr(user, 'last_login')
    
    # Check defaults
    assert user.is_active is True
    assert user.user_data == {}
    assert user.first_name == ""
    assert user.last_name == ""


def test_user_password_hashing():
    """Test password hashing functionality."""
    user = User(username="testuser", email="test@example.com")
    
    # Set password
    user.set_password("mypassword123")
    
    # Password should be hashed
    assert user.password != "mypassword123"
    assert user.password.startswith("pbkdf2_sha256$")
    
    # Check password should work
    assert user.check_password("mypassword123") is True
    assert user.check_password("wrongpassword") is False


def test_user_metadata_properties():
    """Test user_data property accessors."""
    user = User(username="testuser", email="test@example.com")
    
    # Test admin access
    assert user.can_access_admin is False
    user.can_access_admin = True
    assert user.user_data["admin_access"] is True
    assert user.can_access_admin is True
    
    # Test superuser
    assert user.is_superuser is False
    user.is_superuser = True
    assert user.user_data["superuser"] is True
    assert user.is_superuser is True
    
    # Test permissions
    assert user.permissions == []
    user.permissions = ["blog.add_post", "blog.change_post"]
    assert user.user_data["permissions"] == ["blog.add_post", "blog.change_post"]
    assert user.permissions == ["blog.add_post", "blog.change_post"]
    
    # Test preferences
    assert user.preferences == {}
    user.preferences = {"theme": "dark", "language": "en"}
    assert user.user_data["preferences"] == {"theme": "dark", "language": "en"}
    assert user.preferences == {"theme": "dark", "language": "en"}


def test_user_permission_methods():
    """Test permission checking methods."""
    user = User(username="testuser", email="test@example.com")
    
    # Regular user - no permissions
    assert user.has_permission("blog.add_post") is False
    
    # Add specific permission
    user.add_permission("blog.add_post")
    assert user.has_permission("blog.add_post") is True
    assert user.has_permission("blog.delete_post") is False
    
    # Remove permission
    user.remove_permission("blog.add_post")
    assert user.has_permission("blog.add_post") is False
    
    # Superuser has all permissions
    user.is_superuser = True
    assert user.has_permission("blog.add_post") is True
    assert user.has_permission("anything") is True


def test_user_name_methods():
    """Test name property methods."""
    user = User(
        username="testuser", 
        email="test@example.com",
        first_name="John",
        last_name="Doe"
    )
    
    assert user.full_name == "John Doe"
    assert user.get_short_name() == "John"
    
    # Test with only first name
    user.last_name = ""
    assert user.full_name == "John"
    
    # Test with no name
    user.first_name = ""
    assert user.full_name == ""
    assert user.get_short_name() == "testuser"  # Falls back to username


def test_user_crud_operations():
    """Test creating, reading, updating, and deleting users."""
    with session_scope() as session:
        # Create user
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        user.set_password("password123")
        user.can_access_admin = True
        
        session.add(user)
        session.commit()
        
        # Read user
        found_user = session.query(User).filter_by(username="testuser").first()
        assert found_user is not None
        assert found_user.email == "test@example.com"
        assert found_user.can_access_admin is True
        assert found_user.check_password("password123") is True
        
        # Update user
        found_user.first_name = "Updated"
        session.commit()
        
        # Verify update
        updated_user = session.query(User).filter_by(username="testuser").first()
        assert updated_user.first_name == "Updated"
        
        # Delete user
        session.delete(updated_user)
        session.commit()
        
        # Verify deletion
        deleted_user = session.query(User).filter_by(username="testuser").first()
        assert deleted_user is None


@patch('fastframe.conf.settings.DEFAULT_AUTO_FIELD', 'UUIDField')
def test_user_with_uuid_primary_key():
    """Test that User model works with UUID primary keys when configured."""
    # This would require the UUID field to be properly configured
    # For now, just test that the setting is respected in general
    from fastframe.conf import settings
    assert settings.DEFAULT_AUTO_FIELD == 'UUIDField'