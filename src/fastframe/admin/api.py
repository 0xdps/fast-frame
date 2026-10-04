"""Generic CRUD REST API — the shared engine behind both the admin API and
the token-authenticated REST API (:mod:`fastframe.api`).

``_build_crud_router`` is the one implementation of "list/get/create/update
/delete every registered model with pagination, search, sorting, filters,
and validation." Both surfaces reuse the *same* ``admin_site`` registry —
whatever you register with ``admin_site.register(Model, ModelAdmin)`` is
reachable from both — but are gated by different auth dependencies:

* Admin API (``get_admin_api_router``): cookie session, requires
  ``can_access_admin`` (see :mod:`fastframe.admin.auth`).
* Generic REST API (``fastframe.api.get_rest_api_router``): bearer token,
  any active user (see :mod:`fastframe.api.auth`).

Endpoints (relative to whichever prefix the router is mounted at):
    GET    /schema                      All registered models + field schemas.
                                 The admin response also includes ``site``
                                 (``ADMIN_SITE_TITLE`` / ``ADMIN_SITE_HEADER``).
    GET    /counts                      Per-model row counts (single query)
    GET    /{resource}                  List (paging, sort, search, filters)
    GET    /{resource}/{id}             Retrieve one
    POST   /{resource}                  Create (422 on validation error)
    PUT    /{resource}/{id}             Update (422 on validation error)
    DELETE /{resource}/{id}             Delete one
    DELETE /{resource}?ids=a&ids=b      Bulk delete
    GET    /{resource}/choices/{field}  Options for a ForeignKey dropdown

Response shapes (React Admin compatible):
    list:   {"data": [...], "total": N, "page": 1, "perPage": 25}
    single: {"data": {...}}
    errors: 422 {"detail": "...", "errors": {"field": "message"}}

Every create/update/delete is recorded in the audit log (see
:mod:`fastframe.admin.audit`) regardless of which surface triggered it.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError

from fastframe.admin.auth import require_admin_user
from fastframe.admin.serializers import (
    deserialize_payload,
    display_label,
    get_pk_name,
    model_schema,
    resource_name,
    serialize_instance,
    serialize_value,
)
from fastframe.admin.site import ModelAdmin, admin_site
from fastframe.db.session import _get_session_factory, _session_ctx
from fastframe.models.exceptions import DoesNotExist, ValidationError


def _admin_site_branding() -> dict[str, str]:
    """Title and header the admin UI shows, from settings."""
    try:
        from fastframe.conf import settings

        title = getattr(settings, "ADMIN_SITE_TITLE", "FastFrame Admin")
        header = getattr(settings, "ADMIN_SITE_HEADER", "Administration")
    except (ImportError, AttributeError):
        title = "FastFrame Admin"
        header = "Administration"
    return {"title": str(title), "header": str(header)}


def _admin_session():
    """Session dependency for CRUD API endpoints.

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
    """Create the admin REST API router (cookie-session authenticated).

    Whether this is reachable at all is controlled by whether
    ``"fastframe.admin"`` is in ``INSTALLED_APPS`` (see
    :class:`fastframe.admin.apps.AdminConfig`) — not a setting here.
    ``ENABLE_ADMIN_DOCS`` only controls OpenAPI schema visibility for an
    already-enabled admin.
    """
    try:
        from fastframe.conf import settings

        enable_admin_docs = getattr(settings, "ENABLE_ADMIN_DOCS", True)
        admin_api_prefix = getattr(settings, "ADMIN_API_PREFIX", "/api/admin")
    except (ImportError, AttributeError):
        enable_admin_docs = True
        admin_api_prefix = "/api/admin"

    return _build_crud_router(
        prefix=admin_api_prefix,
        tags=["admin-api"],
        include_in_schema=enable_admin_docs,
        auth_dependency=require_admin_user,
        source="admin",
    )


def _build_crud_router(
    *,
    prefix: str,
    tags: list[str],
    include_in_schema: bool,
    auth_dependency: Callable[..., Any],
    source: str,
) -> APIRouter:
    """Build a full CRUD router over ``admin_site``'s registry.

    Args:
        prefix: URL prefix to mount at (e.g. ``/api/admin`` or ``/api/v1``).
        tags: OpenAPI tags for these routes.
        include_in_schema: Whether to show these routes in OpenAPI.
        auth_dependency: FastAPI dependency callable. Must return the
            authenticated user (or raise ``HTTPException`` on failure) —
            the return value is used for audit-log attribution.
        source: Short label recorded on audit-log entries (e.g. ``"admin"``
            or ``"api"``) so you can tell which surface made a change.
    """
    # All routes below require authentication — login/logout/me (admin) or
    # token obtain/revoke (REST API) live on separate, unprotected routers.
    router = APIRouter(
        prefix=prefix,
        tags=tags,
        include_in_schema=include_in_schema,
        dependencies=[Depends(auth_dependency)],
    )

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------

    @router.get("/schema")
    async def get_schema(
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """Return metadata for every registered model.

        The bundled admin UI uses this single call to auto-configure resources,
        forms, list columns, filters, and permissions. It is purely
        descriptor data — no database queries per model, and it is stable
        for the lifetime of the process (models are registered at import
        time), so it can safely be cached/re-served without re-processing.

        Per-model row counts intentionally live on the separate ``/counts``
        endpoint (one combining query), so this endpoint never triggers a
        ``COUNT(*)`` per model and never changes shape just because rows
        were added or removed.
        """
        registry = admin_site.get_registry()
        payload: dict[str, Any] = {
            "models": [model_schema(model, model_admin, current_user) for model, model_admin in registry.items()]
        }
        if source == "admin":
            payload["site"] = _admin_site_branding()
        return payload

    # ------------------------------------------------------------------
    # Counts
    # ------------------------------------------------------------------

    @router.get("/counts")
    async def get_counts(
        request: Request,
        session=Depends(_admin_session),
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """Return ``{resource: row_count}`` for every model the caller may view.

        Computed with a single combined SQL round trip for the common case
        (models with the default, unfiltered queryset); a model with a
        custom ``get_queryset()`` override is counted individually through
        that queryset instead, and a model the caller lacks view permission
        for is omitted entirely — the same authorization ``/{resource}``
        enforces. The dashboard calls this once, separately from
        ``/schema``, so the (stable, cacheable) schema is never re-sent just
        because row counts changed.
        """
        _session_ctx.set(session)
        registry = admin_site.get_registry()
        return {"counts": _resource_counts(session, registry, current_user, request)}

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
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """List records with pagination, sorting, search, and field filters."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.get_has_view_permission(current_user):
            raise HTTPException(status_code=403, detail="Permission denied")

        qs = model_admin.get_queryset(request)

        # Full-text-ish search across search_fields
        if q:
            qs = model_admin.get_search_results(qs, q)

        # Field filters: any query param matching a field (supports __lookups)
        reserved = {"page", "perPage", "sortField", "sortOrder", "q"}
        filter_kwargs = {key: value for key, value in request.query_params.items() if key not in reserved}
        if filter_kwargs:
            qs = qs.filter(**filter_kwargs)

        total = qs.count()

        # Sorting (M2M fields aren't real columns, so they can't be sorted on)
        from fastframe.models.fields import ManyToManyField

        sort_field_obj = model._meta["fields"].get(sortField) if sortField else None
        sortable = sort_field_obj is not None and not isinstance(sort_field_obj, ManyToManyField)
        if sortField and sortable:
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
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """Return {value, label} options for a ForeignKey field."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.get_has_view_permission(current_user):
            raise HTTPException(status_code=403, detail="Permission denied")

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
            {"value": serialize_value(getattr(obj, target_pk)), "label": display_label(obj)} for obj in qs.limit(limit)
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
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """Retrieve a single record."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.get_has_view_permission(current_user):
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
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """Create a record. Returns 422 with per-field errors on validation failure."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.get_has_add_permission(current_user):
            raise HTTPException(status_code=403, detail="Permission denied")

        payload = await _json_body(request)

        try:
            cleaned = deserialize_payload(model, payload)
            cleaned = model_admin.get_editable_fields(cleaned, partial=False)
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

        _audit(
            session,
            user=current_user,
            action="create",
            model=model,
            instance=instance,
            changes={"fields": serialize_instance(instance, include_relations=False)},
            source=source,
        )
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
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """Update a record (partial updates allowed)."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.get_has_change_permission(current_user):
            raise HTTPException(status_code=403, detail="Permission denied")

        payload = await _json_body(request)
        instance = _get_instance(model, record_id)
        before = serialize_instance(instance, include_relations=False)

        try:
            cleaned = deserialize_payload(model, payload, partial=True)
            cleaned = model_admin.get_editable_fields(cleaned, partial=True)
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

        after = serialize_instance(instance, include_relations=False)
        diff = {
            field_name: {"old": before.get(field_name), "new": after.get(field_name)}
            for field_name in cleaned
            if before.get(field_name) != after.get(field_name)
        }
        _audit(
            session,
            user=current_user,
            action="update",
            model=model,
            instance=instance,
            changes=diff,
            source=source,
        )
        return {"data": after}

    # ------------------------------------------------------------------
    # Delete (single + bulk)
    # ------------------------------------------------------------------

    @router.delete("/{resource}/{record_id}")
    async def delete_record(
        resource: str,
        record_id: str,
        session=Depends(_admin_session),
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """Delete a single record."""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.get_has_delete_permission(current_user):
            raise HTTPException(status_code=403, detail="Permission denied")
        instance = _get_instance(model, record_id)
        data = serialize_instance(instance)
        repr_before_delete = str(instance)[:255]

        try:
            session.delete(instance)
            session.flush()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail=_integrity_error_detail("Cannot delete: other records reference this object"),
            ) from e

        _audit(
            session,
            user=current_user,
            action="delete",
            model=model,
            instance=None,
            model_name=model.__name__,
            object_id=str(data.get("id", "")),
            object_repr=repr_before_delete,
            changes={"fields": data},
            source=source,
        )
        return {"data": data}

    @router.delete("/{resource}")
    async def bulk_delete_records(
        resource: str,
        ids: list[str] = Query(...),
        session=Depends(_admin_session),
        current_user: Any = Depends(auth_dependency),
    ) -> dict[str, Any]:
        """Bulk delete: DELETE /api/admin/post?ids=1&ids=2"""
        _session_ctx.set(session)
        model, model_admin = _find_resource(resource)
        if not model_admin.get_has_delete_permission(current_user):
            raise HTTPException(status_code=403, detail="Permission denied")
        pk_name = get_pk_name(model)
        deleted: list[Any] = []

        try:
            for raw_id in ids:
                instance = _get_instance(model, raw_id)
                data = serialize_instance(instance)
                repr_before_delete = str(instance)[:255]
                deleted.append(serialize_value(getattr(instance, pk_name)))
                session.delete(instance)
                _audit(
                    session,
                    user=current_user,
                    action="delete",
                    model=model,
                    instance=None,
                    model_name=model.__name__,
                    object_id=str(data.get("id", "")),
                    object_repr=repr_before_delete,
                    changes={"fields": data},
                    source=source,
                )
            session.flush()
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(
                status_code=409,
                detail=_integrity_error_detail("Cannot delete: other records reference these objects"),
            ) from e

        return {"data": deleted}

    return router


def _validation_error_detail(e: ValidationError) -> dict:
    return {"message": "Validation failed", "errors": e.errors or {"__all__": str(e)}}


def _integrity_error_detail(message: str) -> dict:
    return {"message": message, "errors": {}}


def _audit(
    session: Any,
    *,
    user: Any,
    action: str,
    model: type,
    instance: Any,
    changes: dict[str, Any],
    source: str,
    model_name: str | None = None,
    object_id: str | None = None,
    object_repr: str | None = None,
) -> None:
    """Write an audit-log entry. Best-effort — never raises into the request.

    Prefer passing ``instance`` (for create/update, where it's still valid
    after flush); pass explicit ``model_name``/``object_id``/``object_repr``
    for delete, where the instance is gone by the time we log it.
    """
    from fastframe.admin.audit import record_audit

    record_audit(
        session,
        user=user,
        action=action,
        model_name=model_name or model.__name__,
        object_id=object_id if object_id is not None else str(getattr(instance, get_pk_name(model), "") or ""),
        object_repr=object_repr if object_repr is not None else str(instance)[:255],
        changes=changes,
        source=source,
    )


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _resource_counts(session: Any, registry: dict[type, Any], current_user: Any, request: Any = None) -> dict[str, int]:
    """Return ``{resource: row_count}`` for every model the caller may view.

    Two rules, matching ``/{resource}`` (the list endpoint) exactly:

    - A model the caller lacks ``get_has_view_permission`` for is omitted
      entirely — the same authorization ``/{resource}`` enforces, so
      ``/counts`` can't be used to learn row totals for a model a 403
      already hides.
    - A model with a custom (row-filtering) ``get_queryset()`` override is
      counted through that queryset, not the raw table, so its total
      matches what ``/{resource}`` would actually list.

    Models using the default, unfiltered ``get_queryset()`` are still
    counted together in a single combined ``SELECT ... UNION ALL SELECT``
    (one DB round trip for the common case, not one per model). Only
    models with a genuine queryset override cost an extra query each.
    Models whose table has not been created yet (or lacks
    ``__tablename__``) are skipped, so the dashboard degrades gracefully
    during early development before ``manage.py migrate`` has run.
    """
    from sqlalchemy import func, literal, select, union_all
    from sqlalchemy import inspect as sa_inspect

    counts: dict[str, int] = {}
    # (label, Table) pairs for every permitted model with the default,
    # unfiltered queryset — batched into one combined query below.
    labeled_tables: list[tuple[str, Any]] = []

    for model, model_admin in registry.items():
        if not model_admin.get_has_view_permission(current_user):
            continue
        label = resource_name(model)

        if type(model_admin).get_queryset is ModelAdmin.get_queryset:
            try:
                table = sa_inspect(model).local_table
            except Exception:
                continue
            if table is None:
                continue
            labeled_tables.append((label, table))
        else:
            # Custom get_queryset(): may filter rows (e.g. a tenant or
            # "published only" scope), so count it directly rather than
            # the raw table.
            try:
                counts[label] = model_admin.get_queryset(request).count()
            except Exception:
                continue

    if labeled_tables:
        statements = [
            select(literal(label).label("resource"), func.count().label("total")).select_from(table)
            for label, table in labeled_tables
        ]
        combined = union_all(*statements)

        try:
            rows = session.execute(combined).all()
        except Exception:
            # A missing table (or schema drift) breaks the combined query;
            # the models counted individually above are still returned.
            rows = []
        for resource, total in rows:
            counts[str(resource)] = int(total)

    return counts


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
