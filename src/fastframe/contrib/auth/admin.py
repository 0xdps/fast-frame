"""Default admin configuration for FastFrame User model."""

from fastframe.admin import ModelAdmin, admin_site

from .models import User


class UserAdmin(ModelAdmin):
    """Admin interface for the default User model."""
    
    # List page configuration
    list_display = ["username", "email", "first_name", "last_name", "is_active", "date_joined"]
    list_filter = ["is_active", "date_joined"]
    search_fields = ["username", "email", "first_name", "last_name"]
    list_per_page = 50
    
    # Form configuration
    # password field is write_only, so it won't appear in edit forms
    # This is intentional - use the change password action instead
    
    def get_queryset(self, request):
        """Default queryset for user list."""
        return super().get_queryset(request)
    
    def get_search_results(self, qs, search_term):
        """Custom search to include name fields."""
        if search_term:
            return qs.filter(
                username__icontains=search_term
            ) | qs.filter(
                email__icontains=search_term
            ) | qs.filter(
                first_name__icontains=search_term
            ) | qs.filter(
                last_name__icontains=search_term
            )
        return qs


# Register the User model with the admin
# This will only register if AUTH_USER_MODEL points to auth.User
# Custom user models should register themselves
admin_site.register(User, UserAdmin)