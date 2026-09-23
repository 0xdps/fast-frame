"""User admin configuration."""

from fastframe.admin import ModelAdmin, admin_site

from .models import SimpleUser


class SimpleUserAdmin(ModelAdmin):
    list_display = ["first_name", "last_name", "username", "email", "is_active"]
    search_fields = ["first_name", "last_name", "username", "email"]
    list_filter = ["is_active"]
    list_per_page = 50


# Register
admin_site.register(SimpleUser, SimpleUserAdmin)
