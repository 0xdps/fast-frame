"""FastFrame Admin - Django-like admin interface for FastFrame.

Provides an automatic admin interface for CRUD operations on your models.
Inspired by Django Admin but performance-first with SSR + htmx.

Example:
    from fastframe.admin import ModelAdmin, admin_site
    from myapp.models import Post

    class PostAdmin(ModelAdmin):
        list_display = ["title", "author", "created_at"]
        search_fields = ["title", "content"]
        list_filter = ["status", "category"]

    admin_site.register(Post, PostAdmin)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from fastframe.models import Model


class ModelAdmin:
    """Configuration for a model's admin interface.

    Define list views, forms, search, filters, and permissions for a model.
    """

    # Display configuration
    list_display: list[str] = []  # Fields to show in list view
    list_display_links: list[str] | None = None  # Clickable fields (defaults to first)
    list_filter: list[str] = []  # Fields to filter by
    search_fields: list[str] = []  # Fields to search in
    ordering: list[str] | None = None  # Default ordering (uses model Meta if None)
    
    # Pagination
    list_per_page: int = 100  # Items per page
    list_max_show_all: int = 200  # Max items for "show all" link
    
    # Performance
    list_select_related: list[str] | None = None  # Auto-detect if None
    prefetch_related: list[str] = []  # M2M and reverse FKs to prefetch
    
    # Form configuration
    fields: list[str] | None = None  # Fields to show in form (all if None)
    exclude: list[str] = []  # Fields to exclude from form
    readonly_fields: list[str] = []  # Read-only fields
    
    # Detail view
    fieldsets: list[tuple[str | None, dict[str, Any]]] | None = None  # Grouped fields
    
    # Actions
    actions: list[str] = []  # Bulk actions
    actions_on_top: bool = True
    actions_on_bottom: bool = False
    
    # Permissions
    has_add_permission: bool = True
    has_change_permission: bool = True
    has_delete_permission: bool = True
    has_view_permission: bool = True
    
    # Safety features
    confirmation_required: list[str] = ["delete"]  # Actions requiring confirmation
    save_as: bool = False  # "Save as new" button
    save_on_top: bool = False  # Save buttons on top

    def __init__(self, model: type[Model], admin_site: AdminSite) -> None:
        """Initialize the ModelAdmin.

        Args:
            model: The model class this admin is for.
            admin_site: The AdminSite instance registering this admin.
        """
        self.model = model
        self.admin_site = admin_site
        
        # Auto-detect select_related if not specified
        if self.list_select_related is None:
            self.list_select_related = self._auto_detect_select_related()

    def _auto_detect_select_related(self) -> list[str]:
        """Auto-detect ForeignKey fields to select_related.

        Returns:
            List of field names that are ForeignKeys.
        """
        if not hasattr(self.model, "_meta"):
            return []
        
        select_related = []
        for field_name, field in self.model._meta.get("fields", {}).items():
            # Check if it's a ForeignKey
            if hasattr(field, "to") and field_name in self.get_list_display():
                # Get the relationship attribute name
                rel_name = getattr(field, "relationship_name", None)
                if rel_name:
                    select_related.append(rel_name)
        
        return select_related

    def get_list_display(self) -> list[str]:
        """Get fields to display in list view.

        Returns:
            List of field names, or ["__str__"] if not configured.
        """
        return self.list_display or ["__str__"]

    def get_queryset(self, request: Any = None) -> Any:
        """Get the queryset for the list view.

        Override to filter querysets based on request/permissions.

        Args:
            request: The current HTTP request (FastAPI request).

        Returns:
            QuerySet for the model.
        """
        qs = self.model.objects.all()
        
        # Apply select_related for performance
        if self.list_select_related:
            # Note: Our current QuerySet doesn't have select_related yet
            # This is a placeholder for future implementation
            pass
        
        # Apply ordering
        ordering = self.get_ordering()
        if ordering:
            # Note: Our current QuerySet doesn't have order_by yet
            # Uses model Meta ordering for now
            pass
        
        return qs

    def get_ordering(self) -> list[str]:
        """Get the ordering for the queryset.

        Returns:
            List of field names for ordering.
        """
        if self.ordering:
            return self.ordering
        # Use model's Meta ordering
        return self.model._meta.get("ordering", [])

    def get_search_results(self, queryset: Any, search_term: str) -> Any:
        """Filter queryset by search term.

        Args:
            queryset: The base queryset.
            search_term: The search string.

        Returns:
            Filtered queryset.
        """
        if not search_term or not self.search_fields:
            return queryset
        
        # Build Q object for OR search across search_fields
        from fastframe.models import Q
        
        q_objects = []
        for field in self.search_fields:
            # Use icontains for case-insensitive partial match
            q_objects.append(Q(**{f"{field}__icontains": search_term}))
        
        # Combine with OR
        if q_objects:
            combined_q = q_objects[0]
            for q in q_objects[1:]:
                combined_q = combined_q | q
            queryset = queryset.filter(combined_q)
        
        return queryset


class AdminSite:
    """The admin site - a registry of models and their admin classes.

    Usage:
        admin_site = AdminSite(name="admin")
        admin_site.register(MyModel, MyModelAdmin)
    """

    def __init__(self, name: str = "admin") -> None:
        """Initialize the admin site.

        Args:
            name: The name/URL prefix for this admin site.
        """
        self.name = name
        self._registry: dict[type[Model], ModelAdmin] = {}

    def register(
        self,
        model: type[Model],
        admin_class: type[ModelAdmin] | None = None,
    ) -> None:
        """Register a model with the admin site.

        Args:
            model: The model class to register.
            admin_class: Optional ModelAdmin subclass. Uses ModelAdmin if None.

        Raises:
            ValueError: If the model is already registered.
        """
        if model in self._registry:
            raise ValueError(f"Model {model.__name__} is already registered")

        # Use default ModelAdmin if none provided
        if admin_class is None:
            admin_class = ModelAdmin

        # Instantiate the admin class
        admin_instance = admin_class(model=model, admin_site=self)
        self._registry[model] = admin_instance

    def unregister(self, model: type[Model]) -> None:
        """Unregister a model from the admin site.

        Args:
            model: The model class to unregister.

        Raises:
            ValueError: If the model is not registered.
        """
        if model not in self._registry:
            raise ValueError(f"Model {model.__name__} is not registered")

        del self._registry[model]

    def is_registered(self, model: type[Model]) -> bool:
        """Check if a model is registered.

        Args:
            model: The model class to check.

        Returns:
            True if registered, False otherwise.
        """
        return model in self._registry

    def get_model_admin(self, model: type[Model]) -> ModelAdmin:
        """Get the ModelAdmin for a model.

        Args:
            model: The model class.

        Returns:
            The ModelAdmin instance.

        Raises:
            KeyError: If the model is not registered.
        """
        return self._registry[model]

    def get_registry(self) -> dict[type[Model], ModelAdmin]:
        """Get the full registry of models.

        Returns:
            Dictionary mapping model classes to ModelAdmin instances.
        """
        return self._registry.copy()


# Global admin site instance
admin_site = AdminSite()


__all__ = ["ModelAdmin", "AdminSite", "admin_site"]
