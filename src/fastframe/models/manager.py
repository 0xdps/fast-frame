from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.sql import Select

from fastframe.db.session import get_current_session
from fastframe.models.exceptions import DoesNotExist, MultipleObjectsReturned

T = TypeVar("T")


class QuerySet(Generic[T]):
    """Lazy, chainable query builder that acts like a list."""

    def __init__(self, model_class: type[T], stmt: Select[tuple[T]] | None = None) -> None:
        self.model_class = model_class
        self._stmt = stmt if stmt is not None else select(model_class)
        self._result_cache: list[T] | None = None

    @property
    def session(self):
        return get_current_session()

    def _clone(self) -> QuerySet[T]:
        """Create a copy of this queryset with the same statement."""
        return QuerySet(self.model_class, self._stmt)

    def _fetch_all(self) -> list[T]:
        """Execute query and cache results."""
        if self._result_cache is None:
            self._result_cache = list(self.session.scalars(self._stmt).all())
        return self._result_cache

    def filter(self, *args: Any, **kwargs: Any) -> QuerySet[T]:
        """Filter by field conditions. Returns a new QuerySet for chaining.

        Supports:
        - Simple equality: .filter(name="Alice")
        - Field lookups: .filter(age__gte=18, name__icontains="alice")
        - Q objects: .filter(Q(published=True) | Q(featured=True))

        Field lookups:
            - exact: field == value (default)
            - iexact: case-insensitive exact
            - contains, icontains: substring matching
            - gt, gte, lt, lte: comparisons
            - in: field in list
            - isnull: field is NULL
            - startswith, istartswith, endswith, iendswith: string matching
        """
        from fastframe.models.query import Q, _apply_lookup

        clone = self._clone()

        # Handle Q objects
        for q_obj in args:
            if isinstance(q_obj, Q):
                clone._stmt = clone._stmt.where(q_obj.to_sqlalchemy(self.model_class))

        # Handle field lookups
        for key, value in kwargs.items():
            if "__" in key:
                # Field lookup like "age__gte"
                field_name, lookup = key.rsplit("__", 1)
                column = getattr(self.model_class, field_name)
                clone._stmt = clone._stmt.where(_apply_lookup(column, lookup, value))
            else:
                # Simple equality
                clone._stmt = clone._stmt.where(getattr(self.model_class, key) == value)

        return clone

    def exclude(self, **kwargs: Any) -> QuerySet[T]:
        """Exclude rows matching field equality. Returns a new QuerySet for chaining."""
        clone = self._clone()
        for key, value in kwargs.items():
            clone._stmt = clone._stmt.where(getattr(self.model_class, key) != value)
        return clone

    def order_by(self, *fields: str) -> QuerySet[T]:
        """Order by one or more fields. Prefix with '-' for descending.
        
        Example: .order_by('-created_at', 'id')
        """
        clone = self._clone()
        for field in fields:
            if field.startswith("-"):
                column = getattr(self.model_class, field[1:])
                clone._stmt = clone._stmt.order_by(column.desc())
            else:
                column = getattr(self.model_class, field)
                clone._stmt = clone._stmt.order_by(column)
        return clone

    def limit(self, n: int) -> QuerySet[T]:
        """Limit results to n rows."""
        clone = self._clone()
        clone._stmt = clone._stmt.limit(n)
        return clone

    def offset(self, n: int) -> QuerySet[T]:
        """Skip first n rows."""
        clone = self._clone()
        clone._stmt = clone._stmt.offset(n)
        return clone

    def get(self, **kwargs: Any) -> T:
        """Get a single object matching kwargs. Raises DoesNotExist or MultipleObjectsReturned."""
        matches = self.filter(**kwargs)._fetch_all()
        if not matches:
            raise DoesNotExist(f"{self.model_class.__name__} matching {kwargs!r} does not exist.")
        if len(matches) > 1:
            raise MultipleObjectsReturned(
                f"{self.model_class.__name__} matching {kwargs!r} returned {len(matches)} rows."
            )
        return matches[0]

    def first(self) -> T | None:
        """Return the first result or None."""
        result = self.session.scalars(self._stmt.limit(1)).first()
        return result

    def exists(self) -> bool:
        """Return True if the query matches any rows."""
        stmt = select(func.count()).select_from(self._stmt.subquery())
        result = self.session.scalar(stmt)
        return int(result or 0) > 0

    def count(self) -> int:
        """Return the count of matching rows."""
        stmt = select(func.count()).select_from(self._stmt.subquery())
        result = self.session.scalar(stmt)
        return int(result or 0)

    # List-like interface for backward compatibility
    def __iter__(self):
        return iter(self._fetch_all())

    def __len__(self) -> int:
        return len(self._fetch_all())

    def __getitem__(self, key):
        return self._fetch_all()[key]

    def __repr__(self) -> str:
        return f"<QuerySet: {self._fetch_all()!r}>"


class Manager(Generic[T]):
    def __init__(self, model_class: type[T]) -> None:
        self.model_class = model_class

    @property
    def session(self):
        return get_current_session()

    def all(self) -> QuerySet[T]:
        """Return a QuerySet for all objects."""
        return QuerySet(self.model_class)

    def filter(self, *args: Any, **kwargs: Any) -> QuerySet[T]:
        """Return a QuerySet filtered by field conditions."""
        return self.all().filter(*args, **kwargs)

    def exclude(self, **kwargs: Any) -> QuerySet[T]:
        """Return a QuerySet excluding objects matching field equality."""
        return self.all().exclude(**kwargs)

    def order_by(self, *fields: str) -> QuerySet[T]:
        """Return a QuerySet ordered by fields."""
        return self.all().order_by(*fields)

    def get(self, **kwargs: Any) -> T:
        """Get a single object. Raises DoesNotExist or MultipleObjectsReturned."""
        return self.all().get(**kwargs)

    def first(self) -> T | None:
        """Return the first object or None."""
        return self.all().first()

    def exists(self) -> bool:
        """Return True if any objects exist."""
        return self.all().exists()

    def count(self) -> int:
        """Return the count of all objects."""
        return self.all().count()

    def create(self, **kwargs: Any) -> T:
        """Create and flush a new object."""
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance
