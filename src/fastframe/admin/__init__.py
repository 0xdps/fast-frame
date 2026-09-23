"""FastFrame Admin - Django-like admin interface.

Provides automatic CRUD interface for your models with:
- List views with search, filters, and pagination
- Create/Edit forms with validation
- Delete confirmations
- Performance optimizations (auto select_related, limits)
- SSR-first with htmx for progressive enhancement

Usage:
    # In your app's admin.py
    from fastframe.admin import ModelAdmin, admin_site
    from myapp.models import Post

    class PostAdmin(ModelAdmin):
        list_display = ["title", "author", "status", "created_at"]
        search_fields = ["title", "content"]
        list_filter = ["status", "category"]
        list_per_page = 50

    admin_site.register(Post, PostAdmin)

    # In your main app
    from fastframe.admin import get_admin_router
    app.include_router(get_admin_router())

Then visit http://localhost:8000/admin/
"""

from fastframe.admin.site import AdminSite, ModelAdmin, admin_site
from fastframe.admin.views import get_admin_router

__all__ = [
    "AdminSite",
    "ModelAdmin", 
    "admin_site",
    "get_admin_router",
]
