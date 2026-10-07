from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.sql import Select

from fastframe.db.session import get_current_session
from fastframe.models.exceptions import DoesNotExist, MultipleObjectsReturned

T = TypeVar("T")


def _chained_load_option(model_class: type, path: str, loader: Any) -> Any:
    """Build a (possibly nested) SQLAlchemy loader option from a Django-style
    ``a__b__c`` relationship path, e.g. ``joinedload(Post.author).joinedload(Author.profile)``.
    """
    parts = path.split("__")
    current_cls = model_class
    attr = getattr(current_cls, parts[0])
    option = loader(attr)
    current_cls = attr.property.mapper.class_
    for part in parts[1:]:
        attr = getattr(current_cls, part)
        # Chain onto the same Load option (e.g. joinedload(A.b).joinedload(B.c))
        # via the method of the same name as the loader function.
        option = getattr(option, loader.__name__)(attr)
        current_cls = attr.property.mapper.class_
    return option


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
        - F() values, to compare two columns: .filter(karma__gt=F("num_posts"))

        Field lookups:
            - exact: field == value (default)
            - iexact: case-insensitive exact
            - contains, icontains: substring matching
            - gt, gte, lt, lte: comparisons
            - in: field in list
            - isnull: field is NULL
            - startswith, istartswith, endswith, iendswith: string matching
        """
        from fastframe.models.query import Q, lookup_expr, resolve_value

        clone = self._clone()

        # Handle Q objects
        for q_obj in args:
            if isinstance(q_obj, Q):
                clone._stmt = clone._stmt.where(q_obj.to_sqlalchemy(self.model_class))

        for key, value in kwargs.items():
            clone._stmt = clone._stmt.where(lookup_expr(self.model_class, key, resolve_value(value, self.model_class)))

        return clone

    def exclude(self, **kwargs: Any) -> QuerySet[T]:
        """Exclude rows matching field equality. Returns a new QuerySet for chaining."""
        from fastframe.models.query import resolve_value

        clone = self._clone()
        for key, value in kwargs.items():
            value = resolve_value(value, self.model_class)
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

    def select_related(self, *fields: str) -> QuerySet[T]:
        """Eager-load related objects via a SQL JOIN (one query total).

        For ForeignKey / one-to-one style relationships — anything where
        each row has exactly one related object. Without this, accessing
        a relationship attribute on each result (e.g. ``post.author`` in a
        loop) issues one extra query *per row* (the classic N+1 problem).

        Supports Django-style ``__`` nesting for related-of-related
        access: ``.select_related("author__profile")``.

        Example: ``Post.objects.select_related("author")``
        """
        from sqlalchemy.orm import joinedload

        clone = self._clone()
        for field in fields:
            clone._stmt = clone._stmt.options(_chained_load_option(self.model_class, field, joinedload))
        return clone

    def prefetch_related(self, *fields: str) -> QuerySet[T]:
        """Eager-load related objects via a separate, batched query.

        For reverse-FK / many-to-many style relationships — anything where
        each row can have *many* related objects, where a JOIN would
        duplicate rows. Uses ``SELECT ... WHERE fk IN (...)`` under the
        hood instead, avoiding N+1 the same way ``select_related`` does,
        with a strategy suited to collections.

        Supports Django-style ``__`` nesting: ``.prefetch_related("posts__tags")``.

        Example: ``Author.objects.prefetch_related("posts")``
        """
        from sqlalchemy.orm import selectinload

        clone = self._clone()
        for field in fields:
            clone._stmt = clone._stmt.options(_chained_load_option(self.model_class, field, selectinload))
        return clone

    def only(self, *fields: str) -> QuerySet[T]:
        """Load only these columns eagerly; every other column is fetched
        lazily on first access (one extra query each, the first time
        it's touched).

        Still returns full model instances, unlike :meth:`values`/
        :meth:`values_list` — use this to shrink a SELECT for large
        columns you don't always need while keeping the normal object API.

        Example: ``Post.objects.only("id", "title")``
        """
        from sqlalchemy.orm import load_only

        clone = self._clone()
        columns = [getattr(self.model_class, field) for field in fields]
        clone._stmt = clone._stmt.options(load_only(*columns))
        return clone

    def defer(self, *fields: str) -> QuerySet[T]:
        """Skip loading these columns eagerly; they're fetched lazily on
        first access instead. The inverse of :meth:`only` — use this to
        exclude a couple of large/rarely-needed columns instead of
        listing every other one.

        Example: ``Post.objects.defer("body")``
        """
        from sqlalchemy.orm import defer as sa_defer

        clone = self._clone()
        for field in fields:
            column = getattr(self.model_class, field)
            clone._stmt = clone._stmt.options(sa_defer(column))
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

    def update(self, **kwargs: Any) -> int:
        """Update every row matching this QuerySet in a single UPDATE
        statement — without loading matching objects into Python first.

        Supports F() values for atomic column-to-column updates, e.g.
        ``Post.objects.filter(author_id=1).update(views=F("views") + 1)``.

        Returns the number of matched rows. Bypasses per-instance ORM
        events/hooks (there's no ``instance.save()`` call per row) — use
        a loop with ``.save()`` instead if you rely on those.
        """
        from sqlalchemy import update as sa_update

        from fastframe.models.query import resolve_value

        resolved = {key: resolve_value(value, self.model_class) for key, value in kwargs.items()}
        stmt = sa_update(self.model_class).values(**resolved)
        if self._stmt.whereclause is not None:
            stmt = stmt.where(self._stmt.whereclause)

        # Executed directly (not queued like session.add()) — no separate
        # flush() needed, and one would risk also flushing unrelated
        # pending changes on other objects tracked by this session.
        result = self.session.execute(stmt)
        self._result_cache = None
        return result.rowcount

    def delete(self) -> int:
        """Delete every row matching this QuerySet in a single DELETE
        statement — without loading matching objects into Python first.

        Returns the number of matched rows. Bypasses per-instance ORM
        events/hooks (there's no ``instance.delete()`` call per row) — use
        a loop with ``.delete()`` instead if you rely on those (e.g.
        cascades modeled only at the ORM level, not via ``ondelete=``).
        """
        from sqlalchemy import delete as sa_delete

        stmt = sa_delete(self.model_class)
        if self._stmt.whereclause is not None:
            stmt = stmt.where(self._stmt.whereclause)

        result = self.session.execute(stmt)
        self._result_cache = None
        return result.rowcount

    def values(self, *fields: str) -> ValuesQuerySet:
        """Return dicts instead of model instances, keeping the same
        filters/ordering — the query only ever fetches these columns,
        never instantiating a full model object.

        No fields given -> every column. Example:
            Post.objects.filter(published=True).values("id", "title")
            # -> [{"id": 1, "title": "..."}, ...]
        """
        return ValuesQuerySet(self, fields, flat=False, as_tuple=False)

    def values_list(self, *fields: str, flat: bool = False) -> ValuesQuerySet:
        """Return tuples instead of model instances (or bare scalars if
        ``flat=True``, which requires exactly one field) — same rationale
        as :meth:`values`.

        Example:
            Post.objects.values_list("id", "title")   # -> [(1, "..."), ...]
            Post.objects.values_list("id", flat=True)  # -> [1, 2, 3, ...]
        """
        if flat and len(fields) != 1:
            raise TypeError("flat=True requires exactly one field in values_list().")
        return ValuesQuerySet(self, fields, flat=flat, as_tuple=True)

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


class ValuesQuerySet:
    """Lazy, list-like result of :meth:`QuerySet.values`/:meth:`QuerySet.values_list`.

    Carries the same filtering/ordering as the ``QuerySet`` it came from,
    but the underlying SELECT only fetches the requested columns and never
    instantiates full model objects — cheaper than ``QuerySet`` when you
    only need a few fields (e.g. building a dropdown of ``(id, name)``
    pairs) or want plain, JSON-serializable dicts.
    """

    def __init__(self, queryset: QuerySet[Any], fields: tuple[str, ...], *, flat: bool, as_tuple: bool) -> None:
        self._queryset = queryset
        self._fields = fields
        self._flat = flat
        self._as_tuple = as_tuple
        self._result_cache: list[Any] | None = None

    def _columns_and_names(self) -> tuple[list[Any], list[str]]:
        model_class = self._queryset.model_class
        if self._fields:
            names = list(self._fields)
            columns = [getattr(model_class, name) for name in names]
        else:
            columns = list(model_class.__table__.columns)
            names = [col.name for col in columns]
        return columns, names

    def _fetch_all(self) -> list[Any]:
        if self._result_cache is None:
            columns, names = self._columns_and_names()
            stmt = self._queryset._stmt.with_only_columns(*columns)
            rows = self._queryset.session.execute(stmt).all()
            if self._as_tuple:
                if self._flat:
                    self._result_cache = [row[0] for row in rows]
                else:
                    self._result_cache = [tuple(row) for row in rows]
            else:
                self._result_cache = [dict(zip(names, row, strict=True)) for row in rows]
        return self._result_cache

    def __iter__(self):
        return iter(self._fetch_all())

    def __len__(self) -> int:
        return len(self._fetch_all())

    def __getitem__(self, key):
        return self._fetch_all()[key]

    def __repr__(self) -> str:
        return f"<ValuesQuerySet: {self._fetch_all()!r}>"


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

    def select_related(self, *fields: str) -> QuerySet[T]:
        """Return a QuerySet with related objects eager-loaded via JOIN."""
        return self.all().select_related(*fields)

    def prefetch_related(self, *fields: str) -> QuerySet[T]:
        """Return a QuerySet with related objects eager-loaded via a batched query."""
        return self.all().prefetch_related(*fields)

    def only(self, *fields: str) -> QuerySet[T]:
        """Return a QuerySet loading only these columns eagerly. See :meth:`QuerySet.only`."""
        return self.all().only(*fields)

    def defer(self, *fields: str) -> QuerySet[T]:
        """Return a QuerySet skipping these columns eagerly. See :meth:`QuerySet.defer`."""
        return self.all().defer(*fields)

    def values(self, *fields: str) -> ValuesQuerySet:
        """Return dicts of every object's fields. See :meth:`QuerySet.values`."""
        return self.all().values(*fields)

    def values_list(self, *fields: str, flat: bool = False) -> ValuesQuerySet:
        """Return tuples of every object's fields. See :meth:`QuerySet.values_list`."""
        return self.all().values_list(*fields, flat=flat)

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

    def get_or_create(self, defaults: dict[str, Any] | None = None, **kwargs: Any) -> tuple[T, bool]:
        """Look up an object matching ``kwargs``; create it if missing.

        ``defaults`` supplies extra fields used only when creating (not
        part of the lookup). Returns ``(object, created)`` — ``created``
        is ``True`` if a new row was inserted.

        Not race-safe under concurrent writers without a matching unique
        constraint: a row inserted concurrently, between the lookup and
        the create, can still raise an ``IntegrityError`` here — catch
        that and retry ``get()`` if you need to handle it.
        """
        try:
            return self.get(**kwargs), False
        except DoesNotExist:
            return self.create(**kwargs, **(defaults or {})), True

    def update_or_create(self, defaults: dict[str, Any] | None = None, **kwargs: Any) -> tuple[T, bool]:
        """Look up an object matching ``kwargs``; update it with
        ``defaults`` if found, else create it (with ``kwargs`` + ``defaults``).

        Returns ``(object, created)``. Same race-condition caveat as
        :meth:`get_or_create`.
        """
        defaults = defaults or {}
        try:
            instance = self.get(**kwargs)
            for key, value in defaults.items():
                setattr(instance, key, value)
            instance.save()
            return instance, False
        except DoesNotExist:
            return self.create(**kwargs, **defaults), True

    def update(self, **kwargs: Any) -> int:
        """Update every row of this model in a single UPDATE statement.

        Shorthand for ``.all().update(...)`` — see :meth:`QuerySet.update`.
        """
        return self.all().update(**kwargs)

    def delete(self) -> int:
        """Delete every row of this model in a single DELETE statement.

        Shorthand for ``.all().delete()`` — see :meth:`QuerySet.delete`.
        """
        return self.all().delete()

    def bulk_create(self, objects: list[T], batch_size: int | None = None) -> list[T]:
        """Insert many objects in as few round-trips as possible.

        Uses SQLAlchemy's own multi-row INSERT batching (``add_all`` +
        ``flush``) — far fewer round-trips than calling ``.save()`` in a
        loop (one INSERT per object) — while still populating
        auto-generated primary keys back onto each object afterward.

        ``batch_size`` splits ``objects`` into chunks of that size (bounds
        memory / a single statement's parameter count for very large
        lists); ``None`` (the default) flushes everything at once.
        """
        if not objects:
            return []
        chunks = (
            [objects] if not batch_size else [objects[i : i + batch_size] for i in range(0, len(objects), batch_size)]
        )
        for chunk in chunks:
            self.session.add_all(chunk)
            self.session.flush()
        return objects

    def bulk_update(self, objects: list[T], fields: list[str], batch_size: int | None = None) -> int:
        """Update specific fields on many existing objects in as few
        round-trips as possible.

        Unlike calling ``.save()`` per object (one UPDATE per object),
        this issues a single batched UPDATE per chunk, using SQLAlchemy's
        "ORM bulk UPDATE by primary key" — every object in ``objects``
        must already have a primary key set. ``fields`` lists which
        attributes to write, same shape as Django's ``bulk_update`` — same
        rationale as ``bulk_create``'s ``batch_size``.

        Returns the number of objects given (not rows actually matched —
        use plain ``QuerySet.update()`` if you need that).

        Only ``fields`` are written to the database. Any *other* attribute
        you've changed on these same objects in memory is discarded (each
        object is fully expired afterward) rather than silently persisted
        by some later, unrelated flush — call ``.save()`` on those
        separately if you need them written too.
        """
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy import update as sa_update

        if not objects:
            return 0
        pk_columns = list(sa_inspect(self.model_class).primary_key)
        if len(pk_columns) != 1:
            raise ValueError("bulk_update() requires a model with a single-column primary key.")
        pk_name = pk_columns[0].name

        chunks = (
            [objects] if not batch_size else [objects[i : i + batch_size] for i in range(0, len(objects), batch_size)]
        )
        stmt = sa_update(self.model_class)
        # no_autoflush: otherwise any *other* pending change on these (or
        # other) tracked objects would flush first via the normal
        # per-instance UPDATE path, silently writing more than `fields`
        # before our own statement even runs.
        with self.session.no_autoflush:
            for chunk in chunks:
                params = [{pk_name: getattr(obj, pk_name), **{f: getattr(obj, f) for f in fields}} for obj in chunk]
                self.session.execute(stmt, params)
                for obj in chunk:
                    self.session.expire(obj)
        return len(objects)
