"""Admin views for CRUD operations.

Provides list, detail, create, update, and delete views for registered models.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from fastframe.admin.site import admin_site
from fastframe.db.session import _session_ctx, get_session


# Templates directory
import pathlib

ADMIN_DIR = pathlib.Path(__file__).parent
templates = Jinja2Templates(directory=str(ADMIN_DIR / "templates"))


def get_admin_router() -> APIRouter:
    """Create and return the admin router with all routes.

    Returns:
        FastAPI APIRouter with admin routes.
    """
    router = APIRouter(prefix="/admin", tags=["admin"])

    @router.get("/", response_class=HTMLResponse)
    async def admin_index(request: Request) -> HTMLResponse:
        """Admin home page showing all registered models.

        Args:
            request: The FastAPI request.

        Returns:
            Rendered HTML template.
        """
        registry = admin_site.get_registry()
        
        # Group models by app
        apps: dict[str, list[dict[str, Any]]] = {}
        for model, model_admin in registry.items():
            app_label = model._meta.get("app_label", "Unknown")
            if app_label not in apps:
                apps[app_label] = []
            
            apps[app_label].append({
                "name": model.__name__,
                "verbose_name": model._meta.get("verbose_name", model.__name__),
                "verbose_name_plural": model._meta.get(
                    "verbose_name_plural", f"{model.__name__}s"
                ),
                "url": f"/admin/{app_label}/{model.__name__.lower()}/",
            })
        
        return templates.TemplateResponse(
            request=request,
            name="admin/index.html",
            context={"apps": apps, "title": "Admin Home"},
        )

    @router.get("/{app_label}/{model_name}/", response_class=HTMLResponse)
    async def model_list(
        request: Request,
        app_label: str,
        model_name: str,
        page: int = 1,
        search: str = "",
        session=Depends(get_session),
    ) -> HTMLResponse:
        """List view for a model.

        Args:
            request: The FastAPI request.
            app_label: The app name.
            model_name: The model name (lowercase).
            page: Page number for pagination.
            search: Search query string.
            session: Database session from dependency injection.

        Returns:
            Rendered HTML template with model list.

        Raises:
            HTTPException: If model not found or not registered.
        """
        # Find the model
        model = _find_model(app_label, model_name)
        model_admin = admin_site.get_model_admin(model)
        
        # Get queryset
        qs = model_admin.get_queryset(request)
        
        # Apply search
        if search:
            qs = model_admin.get_search_results(qs, search)
        
        # Get all results (pagination TODO)
        # Execute query with the injected session
        _session_ctx.set(session)
        results = list(qs)
        
        # Get list display fields
        list_display = model_admin.get_list_display()
        
        # Build table data
        table_headers = []
        for field_name in list_display:
            if field_name == "__str__":
                verbose_name = model._meta.get("verbose_name", model.__name__)
            elif field_name in model._meta.get("fields", {}):
                field = model._meta["fields"][field_name]
                verbose_name = field.verbose_name or field_name.replace("_", " ").title()
            else:
                verbose_name = field_name.replace("_", " ").title()
            table_headers.append(verbose_name)
        
        # Build table rows
        table_rows = []
        for obj in results:
            row = []
            for field_name in list_display:
                if field_name == "__str__":
                    value = str(obj)
                else:
                    value = getattr(obj, field_name, "")
                    # Handle ForeignKey - get related object's string
                    if hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool)):
                        value = str(value)
                row.append(value)
            table_rows.append({"data": row, "pk": obj.id if hasattr(obj, "id") else None})
        
        return templates.TemplateResponse(
            request=request,
            name="admin/model_list.html",
            context={
                "model": model,
                "model_admin": model_admin,
                "title": f"{model._meta.get('verbose_name_plural', f'{model.__name__}s')}",
                "app_label": app_label,
                "model_name": model_name,
                "table_headers": table_headers,
                "table_rows": table_rows,
                "search": search,
                "has_add_permission": model_admin.has_add_permission,
            },
        )

    @router.get("/{app_label}/{model_name}/add/", response_class=HTMLResponse)
    async def model_add(
        request: Request,
        app_label: str,
        model_name: str,
    ) -> HTMLResponse:
        """Add/create view for a model.

        Args:
            request: The FastAPI request.
            app_label: The app name.
            model_name: The model name (lowercase).

        Returns:
            Rendered HTML template with form.
        """
        model = _find_model(app_label, model_name)
        model_admin = admin_site.get_model_admin(model)
        
        if not model_admin.has_add_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        return templates.TemplateResponse(
            request=request,
            name="admin/model_form.html",
            context={
                "model": model,
                "model_admin": model_admin,
                "title": f"Add {model._meta.get('verbose_name', model.__name__)}",
                "app_label": app_label,
                "model_name": model_name,
                "is_add": True,
            },
        )

    @router.get("/{app_label}/{model_name}/{pk}/", response_class=HTMLResponse)
    async def model_detail(
        request: Request,
        app_label: str,
        model_name: str,
        pk: str,
    ) -> HTMLResponse:
        """Detail/edit view for a model instance.

        Args:
            request: The FastAPI request.
            app_label: The app name.
            model_name: The model name (lowercase).
            pk: Primary key of the instance.

        Returns:
            Rendered HTML template with form.
        """
        model = _find_model(app_label, model_name)
        model_admin = admin_site.get_model_admin(model)
        
        if not model_admin.has_change_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Get the instance
        obj = model.objects.get(pk)
        if not obj:
            raise HTTPException(status_code=404, detail="Object not found")
        
        return templates.TemplateResponse(
            request=request,
            name="admin/model_form.html",
            context={
                "model": model,
                "model_admin": model_admin,
                "object": obj,
                "title": f"Edit {model._meta.get('verbose_name', model.__name__)}: {obj}",
                "app_label": app_label,
                "model_name": model_name,
                "pk": pk,
                "is_add": False,
            },
        )

    return router


def _find_model(app_label: str, model_name: str) -> type:
    """Find a model by app label and name.

    Args:
        app_label: The app name.
        model_name: The model name (case-insensitive).

    Returns:
        The model class.

    Raises:
        HTTPException: If model not found or not registered.
    """
    registry = admin_site.get_registry()
    
    for model in registry:
        if (
            model._meta.get("app_label", "").lower() == app_label.lower()
            and model.__name__.lower() == model_name.lower()
        ):
            return model
    
    raise HTTPException(
        status_code=404,
        detail=f"Model {app_label}.{model_name} not found or not registered",
    )


__all__ = ["get_admin_router"]
