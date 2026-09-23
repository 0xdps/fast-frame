"""Tests for FastFrame Admin."""

import pytest
from fastapi.testclient import TestClient

from fastframe.admin import ModelAdmin, admin_site
from fastframe.db.session import session_scope
from fastframe.models import Model, fields


@pytest.fixture
def test_model():
    """Create a test model."""
    
    class TestModel(Model):
        id = fields.IntegerField(primary_key=True)
        name = fields.CharField(max_length=100)
        email = fields.EmailField()
        is_active = fields.BooleanField(default=True)
        
        class Meta:
            db_table = "test_admin_models"
            verbose_name = "Test Model"
            verbose_name_plural = "Test Models"
            app_label = "testapp"
    
    return TestModel


@pytest.fixture
def test_admin(test_model):
    """Register test model with admin."""
    
    class TestModelAdmin(ModelAdmin):
        list_display = ["name", "email", "is_active"]
        search_fields = ["name", "email"]
    
    # Register
    if not admin_site.is_registered(test_model):
        admin_site.register(test_model, TestModelAdmin)
    
    yield admin_site.get_model_admin(test_model)
    
    # Cleanup
    if admin_site.is_registered(test_model):
        admin_site.unregister(test_model)


def test_model_admin_init(test_model):
    """Test ModelAdmin initialization."""
    admin = ModelAdmin(model=test_model, admin_site=admin_site)
    
    assert admin.model == test_model
    assert admin.admin_site == admin_site
    assert admin.list_per_page == 100


def test_admin_site_register(test_model):
    """Test registering a model with admin site."""
    
    # Unregister if exists
    if admin_site.is_registered(test_model):
        admin_site.unregister(test_model)
    
    # Register
    admin_site.register(test_model)
    
    assert admin_site.is_registered(test_model)
    model_admin = admin_site.get_model_admin(test_model)
    assert isinstance(model_admin, ModelAdmin)
    
    # Cleanup
    admin_site.unregister(test_model)


def test_admin_site_register_duplicate(test_model):
    """Test that registering same model twice raises error."""
    
    # Unregister if exists
    if admin_site.is_registered(test_model):
        admin_site.unregister(test_model)
    
    admin_site.register(test_model)
    
    with pytest.raises(ValueError, match="already registered"):
        admin_site.register(test_model)
    
    # Cleanup
    admin_site.unregister(test_model)


def test_get_list_display(test_admin):
    """Test get_list_display method."""
    display = test_admin.get_list_display()
    assert display == ["name", "email", "is_active"]


def test_get_list_display_default(test_model):
    """Test default list_display when not configured."""
    admin = ModelAdmin(model=test_model, admin_site=admin_site)
    display = admin.get_list_display()
    assert display == ["__str__"]


def test_search_results(test_model, test_admin):
    """Test search filtering."""
    # This is a basic unit test; integration tests would use actual DB
    qs = test_model.objects
    
    # Empty search should return unchanged
    result = test_admin.get_search_results(qs, "")
    assert result == qs
    
    # Search term should build Q objects (tested separately)
    # For now just ensure it doesn't crash
    result = test_admin.get_search_results(qs, "test")
    assert result is not None
