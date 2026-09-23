"""Admin REST API — JSON endpoints for CRUD on registered models.

Designed for React Admin / Refine style SPAs, but usable by any HTTP client.

Endpoints:
    GET    /api/admin/schema                      All registered models + field schemas
    GET    /api/admin/{resource}                  List (paging, sort, search, filters)
    GET    /api/admin/{resource}/{id}             Retrieve one
    POST   /api/admin/{resource}                  Create (422 on validation error)
    PUT    /api/admin/{resource}/{id}             Update (422 on validation error)
    DELETE /api/admin/{resource}/{id}             Delete one
    DELETE /api/admin/{resource}?ids=a&ids=b      Bulk delete
    GET    /api/admin/{resource}/choices/{field}  Options for a ForeignKey dropdown

Response shapes (React Admin compatible):
    list:   {"data": [...], "total": N, "page": 1, "perPage": 25}
    single: {"data": {...}}
    errors: 422 {"detail": "...", "errors": {"field": "message"}}
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError

from fastframe.admin.serializers import (
    deserialize_payload,
    get_pk_name,
    model_schema,
    resource_name,
    serialize_instance,
    serialize_value,
)
from fastframe.admin.site import admin_site
from fastframe.db.session import _get_session_factory, _session_ctx
from fastframe.models.exceptions import DoesNotExist, ValidationError


def _admin_session():
    """Session dependency for admin API endpoints.

    Unlike get_session(), this avoids ContextVar token reset, which breaks
    when endpoint exceptions cause dependency teardown in a different anyio
    context. The request context is discarded after the request, so leaving
    the var set is safe.
    """
    session = _get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_admin_api_router() -> APIRouter:
    """Create the admin REST API router."""
    try:
        from fastframe.conf import settings
        enable_admin = getattr(settings, 'ENABLE_ADMIN', True)
        enable_admin_docs = getattr(settings, 'ENABLE_ADMIN_DOCS', True)
        admin_api_prefix = getattr(settings, 'ADMIN_API_PREFIX', '/api/admin')
    except (ImportError, AttributeError):
        enable_admin = True
        enable_admin_docs = True
        admin_api_prefix = '/api/admin'
    
    if not enable_admin:
        # Return empty router if admin is disabled
        return APIRouter(prefix=admin_api_prefix, tags=["admin-api"])
    
    # Create router with conditional OpenAPI inclusion
    router = APIRouter(
        prefix=admin_api_prefix, 
        tags=["admin-api"],
        include_in_schema=enable_admin_docs
    )

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    @router.get("/schema")
    async def get_schema() -> dict[str, Any]:
        """Return metadata for every registered model.

        The React admin uses this to auto-configure resources, forms,
        list columns, filters, and permissions.
        """
        registry = admin_site.get_registry()
        return {
            "models": [model_schema(model, model_admin) for model, model_admin in registry.items()]
        }

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    @router.get("/{resource}")
    async def list_records(
        resource: str,
        request: Request,
        page: int = Query(1, ge=1),
        perPage: int = Query(25, ge=1, le=500),
        sortField: str = "",
        sortOrder: str = "ASC",
        q: str = "",
        session=Depends(_admin_session),
    ) -> dict[str, Any]:
        """List records with pagination, sorting, search, and field filters."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)

        qs = model_admin.get_queryset(request)

        # Full-text-ish search across search_fields
        if q:
            qs = model_admin.get_search_results(qs, q)

        # Field filters: any query param matching a field (supports __lookups)
        reserved = {"page", "perPage", "sortField", "sortOrder", "q"}
        filter_kwargs = {
            key: value for key, value in request.query_params.items() if key not in reserved
        }
        if filter_kwargs:
            qs = qs.filter(**filter_kwargs)

        total = qs.count()

        # Sorting
        if sortField and sortField in model._meta["fields"]:
            qs = qs.order_by(f"-{sortField}" if sortOrder.upper() == "DESC" else sortField)
        else:
            for ordering_field in model_admin.get_ordering():
                qs = qs.order_by(ordering_field)

        # Pagination
        offset = (page - 1) * perPage
        records = list(qs.offset(offset).limit(perPage))

        return {
            "data": [serialize_instance(obj) for obj in records],
            "total": total,
            "page": page,
            "perPage": perPage,
        }

    # ------------------------------------------------------------------
    # ForeignKey choices (for dropdowns / autocomplete)
    # ------------------------------------------------------------------

    @router.get("/{resource}/choices/{field_name}")
    async def fk_choices(
        resource: str,
        field_name: str,
        q: str = "",
        limit: int = Query(50, ge=1, le=200),
        session=Depends(_admin_session),
    ) -> dict[str, Any]:
        """Return {value, label} options for a ForeignKey field."""
        _session_ctx.set(session)
        model, _ = _find_resource(resource)

        field = model._meta["fields"].get(field_name)
        if field is None or not hasattr(field, "to"):
            raise HTTPException(status_code=404, detail=f"{field_name} is not a ForeignKey")

        target_model = _resolve_fk_target(model, field)
        target_pk = get_pk_name(target_model)

        qs = target_model.objects.all()
        if q:
            # Search across string-ish fields of the target
            from fastframe.models import Q

            q_objs = [
                Q(**{f"{name}__icontains": q})
                for name, fld in target_model._meta["fields"].items()
                if fld.__class__.__name__ in ("CharField", "TextField", "EmailField")
            ]
            if q_objs:
                combined = q_objs[0]
                for extra in q_objs[1:]:
                    combined = combined | extra
                qs = qs.filter(combined)

        options = [
            {"value": serialize_value(getattr(obj, target_pk)), "label": str(obj)}
            for obj in qs.limit(limit)
        ]
        return {"data": options}

    # ------------------------------------------------------------------
    # Retrieve
    # ------------------------------------------------------------------

    @router.get("/{resource}/{record_id}")
    async def get_record(
        resource: str,
        record_id: str,
        session=Depends(_admin_session),
    ) -> dict[str, Any]:
        """Retrieve a single record."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.has_view_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        instance = _get_instance(model, record_id)
        return {"data": serialize_instance(instance)}

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @router.post("/{resource}", status_code=201)
    async def create_record(
        resource: str,
        request: Request,
        session=Depends(_admin_session),
    ) -> dict[str, Any]:
        """Create a record. Returns 422 with per-field errors on validation failure."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.has_add_permission:
            raise HTTPException(status_code=403, detail="Permission denied")

        payload = await _json_body(request)

        try:
            cleaned = deserialize_payload(model, payload)
            instance = model(**cleaned)
            instance.full_clean()
            session.add(instance)
            session.flush()
        except ValidationError as e:
            session.rollback()
            raise HTTPException(status_code=422, detail=_validation_error_detail(e)) from e
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail=_integrity_error_detail("Integrity error (duplicate or invalid reference)"),
            ) from e

        return {"data": serialize_instance(instance)}

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @router.put("/{resource}/{record_id}")
    async def update_record(
        resource: str,
        record_id: str,
        request: Request,
        session=Depends(_admin_session),
    ) -> dict[str, Any]:
        """Update a record (partial updates allowed)."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.has_change_permission:
            raise HTTPException(status_code=403, detail="Permission denied")

        payload = await _json_body(request)
        instance = _get_instance(model, record_id)

        try:
            cleaned = deserialize_payload(model, payload, partial=True)
            for field_name, value in cleaned.items():
                setattr(instance, field_name, value)
            instance.full_clean()
            session.add(instance)
            session.flush()
        except ValidationError as e:
            session.rollback()
            raise HTTPException(status_code=422, detail=_validation_error_detail(e)) from e
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail=_integrity_error_detail("Integrity error (duplicate or invalid reference)"),
            ) from e

        return {"data": serialize_instance(instance)}

    # ------------------------------------------------------------------
    # Delete (single + bulk)
    # ------------------------------------------------------------------

    @router.delete("/{resource}/{record_id}")
    async def delete_record(
        resource: str,
        record_id: str,
        session=Depends(_admin_session),
    ) -> dict[str, Any]:
        """Delete a single record."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.has_delete_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        instance = _get_instance(model, record_id)
        data = serialize_instance(instance)

        try:
            session.delete(instance)
            session.flush()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail=_integrity_error_detail(
                    "Cannot delete: other records reference this object"
                ),
            ) from e

        return {"data": data}

    @router.delete("/{resource}")
    async def bulk_delete_records(
        resource: str,
        ids: list[str] = Query(...),
        session=Depends(_admin_session),
    ) -> dict[str, Any]:
        """Bulk delete: DELETE /api/admin/post?ids=1&ids=2"""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.has_delete_permission:
            raise HTTPException(status_code=403, detail="Permission denied")
        pk_name = get_pk_name(model)
        deleted: list[Any] = []

        try:
            for raw_id in ids:
                instance = _get_instance(model, raw_id)
                deleted.append(serialize_value(getattr(instance, pk_name)))
                session.delete(instance)
            session.flush()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail=_integrity_error_detail(
                    "Cannot delete: other records reference these objects"
                ),
            ) from e

        return {"data": deleted}

    return router



def _validation_error_detail(e: ValidationError) -> dict:
    return {"message": "Validation failed", "errors": e.errors or {"__all__": str(e)}}


def _integrity_error_detail(message: str) -> dict:
    return {"message": message, "errors": {}}


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _find_resource(resource: str) -> tuple[type, Any]:
    """Resolve a URL resource name to (model, model_admin)."""
    normalized = resource.lower()
    for model, model_admin in admin_site.get_registry().items():
        if resource_name(model) == normalized:
            return model, model_admin
    raise HTTPException(status_code=404, detail=f"Unknown resource: {resource}")


def _get_instance(model: type, record_id: str) -> Any:
    """Fetch one instance by PK, coercing the id to the PK's type."""
    pk_name = get_pk_name(model)
    pk_field = model._meta["fields"][pk_name]

    from fastframe.admin.serializers import deserialize_value

    try:
        coerced = deserialize_value(pk_field, record_id)
    except ValidationError:
        raise HTTPException(status_code=404, detail="Record not found") from None

    try:
        return model.objects.get(**{pk_name: coerced})
    except DoesNotExist:
        raise HTTPException(status_code=404, detail="Record not found") from None


def _resolve_fk_target(model: type, field: Any) -> type:
    """Resolve a ForeignKey's target model class from the SQLAlchemy registry."""
    target_name = field.to if isinstance(field.to, str) else field.to.__name__
    # Handle "app.Model" style references
    target_name = target_name.split(".")[-1]
    for mapper in model.registry.mappers:
        if mapper.class_.__name__ == target_name:
            return mapper.class_
    raise HTTPException(status_code=500, detail=f"Cannot resolve FK target: {field.to}")


async def _json_body(request: Request) -> dict[str, Any]:
    """Parse the request JSON body, ensuring it's an object."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="JSON body must be an object")
    return body


__all__ = ["get_admin_api_router"]
