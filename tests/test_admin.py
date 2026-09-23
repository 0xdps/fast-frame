"""Tests for FastFrame Admin (site registry and ModelAdmin config).

The model is defined once at module level to avoid SQLAlchemy's
"table already defined" errors from re-creating classes per test.
"""

import pytest

from fastframe.admin import ModelAdmin, admin_site
from fastframe.models import Model, fields


class AdminTestModel(Model):
    id = fields.IntegerField(primary_key=True)
    name = fields.CharField(max_length=100)
    email = fields.EmailField()
    is_active = fields.BooleanField(default=True)

    class Meta:
        db_table = "test_admin_models"
        verbose_name = "Test Model"
        verbose_name_plural = "Test Models"
        app_label = "testapp"


@pytest.fixture
def test_admin():
    """Register the test model with a configured ModelAdmin."""

    class AdminTestModelAdmin(ModelAdmin):
        list_display = ["name", "email", "is_active"]
        search_fields = ["name", "email"]

    if not admin_site.is_registered(AdminTestModel):
        admin_site.register(AdminTestModel, AdminTestModelAdmin)

    yield admin_site.get_model_admin(AdminTestModel)

    if admin_site.is_registered(AdminTestModel):
        admin_site.unregister(AdminTestModel)


def test_model_admin_init():
    """Test ModelAdmin initialization."""
    admin = ModelAdmin(model=AdminTestModel, admin_site=admin_site)

    assert admin.model == AdminTestModel
    assert admin.admin_site == admin_site
    assert admin.list_per_page == 100


def test_admin_site_register():
    """Test registering a model with admin site."""
    if admin_site.is_registered(AdminTestModel):
        admin_site.unregister(AdminTestModel)

    admin_site.register(AdminTestModel)

    assert admin_site.is_registered(AdminTestModel)
    model_admin = admin_site.get_model_admin(AdminTestModel)
    assert isinstance(model_admin, ModelAdmin)

    admin_site.unregister(AdminTestModel)


def test_admin_site_register_duplicate():
    """Test that registering same model twice raises error."""
    if admin_site.is_registered(AdminTestModel):
        admin_site.unregister(AdminTestModel)

    admin_site.register(AdminTestModel)

    with pytest.raises(ValueError, match="already registered"):
        admin_site.register(AdminTestModel)

    admin_site.unregister(AdminTestModel)


def test_get_list_display(test_admin):
    """Test get_list_display method."""
    display = test_admin.get_list_display()
    assert display == ["name", "email", "is_active"]


def test_get_list_display_default():
    """Test default list_display when not configured."""
    admin = ModelAdmin(model=AdminTestModel, admin_site=admin_site)
    display = admin.get_list_display()
    assert display == ["__str__"]


def test_search_results(test_admin):
    """Test search filtering."""
    qs = AdminTestModel.objects

    # Empty search should return unchanged
    result = test_admin.get_search_results(qs, "")
    assert result == qs

    # Search term should build Q objects (doesn't need a DB to construct)
    result = test_admin.get_search_results(qs.all(), "test")
    assert result is not None
