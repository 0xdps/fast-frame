"""Reusable pagination dependency, pairing with `QuerySet.limit()`/`.offset()`.

    from fastapi import Depends
    from fastframe.http.pagination import Pagination, pagination

    @router.get("/todos")
    def list_todos(page: Pagination = Depends(pagination)) -> list[dict]:
        todos = page.apply(Todo.objects.order_by("-created_at"))
        return [{"id": t.id, "title": t.title} for t in todos]
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from fastapi import Query

if TYPE_CHECKING:
    from fastframe.models.manager import QuerySet

T = TypeVar("T")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100


@dataclass
class Pagination:
    """Parsed `?limit=&offset=` query params."""

    limit: int
    offset: int

    def apply(self, queryset: QuerySet[T]) -> QuerySet[T]:
        """Return a new QuerySet with this pagination's limit/offset applied."""
        return queryset.limit(self.limit).offset(self.offset)


def pagination(
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT, description="Max rows to return."),
    offset: int = Query(0, ge=0, description="Rows to skip."),
) -> Pagination:
    """FastAPI dependency: `Depends(pagination)` -> `Pagination(limit, offset)`."""
    return Pagination(limit=limit, offset=offset)
