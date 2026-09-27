"""JSON encoding for values returned from FastFrame endpoints.

Models and querysets serialize to JSON-safe dicts. Everything else is left
for FastAPI, including Pydantic models and plain dicts.
"""

from __future__ import annotations

from typing import Any

from fastframe.admin.serializers import serialize_instance
from fastframe.models.base import Model
from fastframe.models.manager import QuerySet


def encode_response(value: Any) -> Any:
    """Return ``value`` in a form FastAPI can JSON-encode.

    A model becomes a dict of its fields. A queryset or a list/tuple of
    models becomes a list of those dicts. Other values pass through.
    """
    if isinstance(value, Model):
        return serialize_instance(value, include_relations=False)
    if isinstance(value, QuerySet):
        return [serialize_instance(item, include_relations=False) for item in value]
    if isinstance(value, (list, tuple)) and _all_models(value):
        return [serialize_instance(item, include_relations=False) for item in value]
    return value


def _all_models(value: list[Any] | tuple[Any, ...]) -> bool:
    return bool(value) and all(isinstance(item, Model) for item in value)
