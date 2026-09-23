"""Blog admin configuration."""

from fastframe.admin import ModelAdmin, admin_site

from .models import Category, Comment, Post, Tag


class CategoryAdmin(ModelAdmin):
    list_display = ["name", "slug", "post_count"]
    search_fields = ["name", "description"]
    list_per_page = 50


class PostAdmin(ModelAdmin):
    list_display = ["title", "status", "is_featured", "view_count", "like_count"]
    search_fields = ["title", "content", "summary"]
    list_filter = ["status", "is_featured"]
    list_per_page = 25


class TagAdmin(ModelAdmin):
    list_display = ["name", "slug", "usage_count"]
    search_fields = ["name"]
    list_per_page = 50


class CommentAdmin(ModelAdmin):
    list_display = ["author_name", "author_email", "is_approved", "like_count"]
    search_fields = ["author_name", "author_email", "content"]
    list_filter = ["is_approved"]
    list_per_page = 50


# Register all models
admin_site.register(Category, CategoryAdmin)
admin_site.register(Post, PostAdmin)
admin_site.register(Tag, TagAdmin)
admin_site.register(Comment, CommentAdmin)
