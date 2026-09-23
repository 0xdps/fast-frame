"""Serialization helpers for the Admin REST API.

Converts model instances to JSON-safe dicts (serialize_instance) and
incoming JSON payloads to Python values for model fields (deserialize_payload).

Handles: UUID, datetime/date, Decimal, JSON, ForeignKey references.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

from fastframe.models import fields as f
from fastframe.models.exceptions import ValidationError

if TYPE_CHECKING:
    from fastframe.models import Model


def serialize_value(value: Any) -> Any:
    """Convert a single Python value to a JSON-safe value."""
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (dict, list)):
        return value
    # Fallback for anything else (e.g. related objects)
    return str(value)


def get_pk_name(model: type[Model]) -> str:
    """Return the primary key field name for a model."""
    for field_name, field in model._meta["fields"].items():
        if field.primary_key:
            return field_name
    return "id"


def serialize_instance(instance: Model, *, include_relations: bool = True) -> dict[str, Any]:
    """Serialize a model instance to a JSON-safe dict.

    - Every field becomes a key with a JSON-safe value.
    - ForeignKey fields (e.g. ``author_id``) serialize to the raw id, and the
      related object is included under the relationship name (e.g. ``author``)
      as ``{"id": ..., "display": "..."}`` for admin display.
    - Always includes an ``id`` key (React Admin requirement).
    """
    data: dict[str, Any] = {}
    model_fields = instance._meta["fields"]

    for field_name, field in model_fields.items():
        if getattr(field, "write_only", False):
            continue
        value = getattr(instance, field_name, None)
        data[field_name] = serialize_value(value)

        if include_relations and isinstance(field, f.ForeignKey) and value is not None:
            rel_name = field.relationship_name or (
                field_name[:-3] if field_name.endswith("_id") else field_name + "_rel"
            )
            try:
                related = getattr(instance, rel_name, None)
            except Exception:
                related = None
            if related is not None:
                rel_pk = get_pk_name(related.__class__)
                data[rel_name] = {
                    "id": serialize_value(getattr(related, rel_pk, None)),
                    "display": str(related),
                }

    # React Admin requires an "id" attribute on every record
    pk_name = get_pk_name(instance.__class__)
    if "id" not in data and pk_name in data:
        data["id"] = data[pk_name]

    return data


def deserialize_value(field: f.Field, value: Any) -> Any:
    """Coerce a JSON value into the Python type a field expects.

    Raises ValidationError with a field-appropriate message on bad input.
    """
    if value is None or value == "":
        if value == "" and isinstance(field, (f.CharField, f.TextField)):
            return value  # empty string is valid for blank-able strings
        return None

    try:
        if isinstance(field, f.UUIDField):
            return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
        if isinstance(field, f.DateTimeField):
            if isinstance(value, datetime):
                return value
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if isinstance(field, f.DateField):
            if isinstance(value, date) and not isinstance(value, datetime):
                return value
            return date.fromisoformat(str(value)[:10])
        if isinstance(field, f.BooleanField):
            if isinstance(value, bool):
                return value
            return str(value).lower() in ("true", "1", "yes", "on")
        if isinstance(field, (f.IntegerField, f.BigIntegerField, f.AutoField, f.BigAutoField)):
            return int(value)
        if isinstance(field, f.FloatField):
            return float(value)
        if isinstance(field, f.DecimalField):
            return Decimal(str(value))
        if isinstance(field, f.JSONField):
            if isinstance(value, (dict, list)):
                return value
            import json

            return json.loads(value)
        if isinstance(field, f.ForeignKey):
            # FK columns store the target PK; coerce int-like or UUID strings
            if isinstance(value, dict):  # accept {"id": ...} from reference inputs
                value = value.get("id")
            if value is None or value == "":
                return None
            try:
                return int(value)
            except (TypeError, ValueError):
                return uuid.UUID(str(value))
    except (ValueError, TypeError, InvalidOperation) as e:
        raise ValidationError(f"Invalid value for {field.verbose_name}: {value!r}") from e

    # CharField, TextField, EmailField, URLField, etc.
    return value


def deserialize_payload(
    model: type[Model],
    payload: dict[str, Any],
    *,
    partial: bool = False,
) -> dict[str, Any]:
    """Convert a JSON payload into model-ready kwargs.

    Args:
        model: The model class.
        payload: Raw JSON dict from the request body.
        partial: If True (updates), only coerce keys present in payload.
                 If False (creates), ignore unknown keys, skip auto PKs.

    Returns:
        Dict of field_name -> coerced Python value.

    Raises:
        ValidationError: With structured ``errors`` dict for 422 responses.
    """
    model_fields = model._meta["fields"]
    cleaned: dict[str, Any] = {}
    errors: dict[str, str] = {}

    for key, raw_value in payload.items():
        if key not in model_fields:
            continue  # ignore unknown keys (e.g. relationship display objects)

        field = model_fields[key]

        # Never accept client-provided auto PKs on create
        if not partial and isinstance(field, (f.AutoField, f.BigAutoField)):
            continue

        try:
            cleaned[key] = deserialize_value(field, raw_value)
        except ValidationError as e:
            errors[key] = str(e)

    if errors:
        raise ValidationError(errors=errors)

    return cleaned


def model_schema(model: type[Model], model_admin: Any = None) -> dict[str, Any]:
    """Build the field schema the React admin needs to render forms/lists."""
    fields_schema: list[dict[str, Any]] = []

    for field_name, field in model._meta["fields"].items():
        schema: dict[str, Any] = {
            "name": field_name,
            "type": field.__class__.__name__,
            "label": field.verbose_name or field_name.replace("_", " ").title(),
            "required": not field.null and not field.blank and field.default is f.NOT_PROVIDED,
            "nullable": field.null,
            "helpText": field.help_text or "",
            "primaryKey": field.primary_key,
        }

        if hasattr(field, "max_length"):
            schema["maxLength"] = field.max_length
        if field.choices:
            schema["choices"] = [{"value": v, "label": label} for v, label in field.choices]
        if isinstance(field, f.ForeignKey):
            schema["reference"] = field.to if isinstance(field.to, str) else field.to.__name__
            schema["relationshipName"] = field.relationship_name
        if isinstance(field, f.DecimalField):
            schema["maxDigits"] = field.max_digits
            schema["decimalPlaces"] = field.decimal_places
        if field.default is not f.NOT_PROVIDED and not callable(field.default):
            schema["default"] = serialize_value(field.default)

        if getattr(field, "write_only", False):
            schema["writeOnly"] = True

        # Auto PKs and auto-timestamps are read-only in forms
        if isinstance(field, (f.AutoField, f.BigAutoField)):
            schema["readOnly"] = True
        if isinstance(field, f.DateTimeField) and (field.auto_now or field.auto_now_add):
            schema["readOnly"] = True

        fields_schema.append(schema)

    result: dict[str, Any] = {
        "name": model.__name__,
        "resource": resource_name(model),
        "label": model._meta.get("verbose_name", model.__name__),
        "labelPlural": model._meta.get("verbose_name_plural", f"{model.__name__}s"),
        "appLabel": model._meta.get("app_label", "app"),
        "pkField": get_pk_name(model),
        "ordering": model._meta.get("ordering", []),
        "fields": fields_schema,
    }

    if model_admin is not None:
        result["listDisplay"] = model_admin.get_list_display()
        result["searchFields"] = model_admin.search_fields
        result["listFilter"] = model_admin.list_filter
        result["listPerPage"] = model_admin.list_per_page
        result["permissions"] = {
            "create": model_admin.has_add_permission,
            "edit": model_admin.has_change_permission,
            "delete": model_admin.has_delete_permission,
            "view": model_admin.has_view_permission,
        }

    return result


def resource_name(model: type[Model]) -> str:
    """URL/resource identifier for a model (e.g. Post -> 'post')."""
    return model.__name__.lower()
