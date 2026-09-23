"""Admin registration for CustomUser."""

from fastframe.admin import ModelAdmin, admin_site

from .models import CustomUser


class CustomUserAdmin(ModelAdmin):
    list_display = ["username", "email", "phone", "is_active"]
    search_fields = ["username", "email", "phone"]
    list_filter = ["is_active"]


admin_site.register(CustomUser, CustomUserAdmin)
