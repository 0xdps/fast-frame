"""Q and F objects for complex queries (Django-style).

Q objects enable complex logical queries (AND, OR, NOT).
F objects reference field values in queries and updates.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import and_, not_, or_
from sqlalchemy.sql import ColumnElement


class Q:
    """Complex query object for combining filters with AND/OR/NOT.

    Example:
        # (published=True AND featured=True) OR (author="Alice")
        Q(published=True, featured=True) | Q(author="Alice")

        # NOT(published=True)
        ~Q(published=True)
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize Q object with field=value conditions."""
        self.conditions = kwargs
        self.connector = "AND"  # Default connector
        self.negated = False
        self.children: list[Q] = []

    def __and__(self, other: Q) -> Q:
        """Combine with AND: q1 & q2."""
        combined = Q()
        combined.connector = "AND"
        combined.children = [self, other]
        return combined

    def __or__(self, other: Q) -> Q:
        """Combine with OR: q1 | q2."""
        combined = Q()
        combined.connector = "OR"
        combined.children = [self, other]
        return combined

    def __invert__(self) -> Q:
        """Negate with NOT: ~q."""
        clone = Q(**self.conditions)
        clone.negated = not self.negated
        clone.connector = self.connector
        clone.children = self.children
        return clone

    def to_sqlalchemy(self, model_class: type) -> ColumnElement[bool]:
        """Convert Q object to SQLAlchemy filter expression."""
        # Base case: simple field=value conditions
        if self.conditions and not self.children:
            filters = [
                lookup_expr(model_class, key, resolve_value(value, model_class))
                for key, value in self.conditions.items()
            ]
            expr = and_(*filters) if len(filters) > 1 else filters[0]
            return not_(expr) if self.negated else expr

        # Recursive case: combine children with connector
        child_exprs = [child.to_sqlalchemy(model_class) for child in self.children]

        if self.connector == "AND":
            expr = and_(*child_exprs)
        elif self.connector == "OR":
            expr = or_(*child_exprs)
        else:
            raise ValueError(f"Unknown connector: {self.connector}")

        return not_(expr) if self.negated else expr

    def __repr__(self) -> str:
        if self.conditions:
            return f"Q({', '.join(f'{k}={v!r}' for k, v in self.conditions.items())})"
        return f"Q({self.connector}: {self.children})"


class F:
    """Reference to a model field value.

    Use for queries and updates that reference field values:

    Example:
        # Get users where karma > num_posts
        User.objects.filter(karma__gt=F("num_posts"))

        # Increment karma by 1
        user.karma = F("karma") + 1
        user.save()
    """

    def __init__(self, field_name: str) -> None:
        """Initialize F object with field name."""
        self.field_name = field_name

    def resolve(self, model_class: type) -> ColumnElement[Any]:
        """Get the SQLAlchemy column for this field."""
        return getattr(model_class, self.field_name)

    def __add__(self, other: Any) -> FExpression:
        """F("field") + 1."""
        return FExpression(self, "+", other)

    def __sub__(self, other: Any) -> FExpression:
        """F("field") - 1."""
        return FExpression(self, "-", other)

    def __mul__(self, other: Any) -> FExpression:
        """F("field") * 2."""
        return FExpression(self, "*", other)

    def __truediv__(self, other: Any) -> FExpression:
        """F("field") / 2."""
        return FExpression(self, "/", other)

    def __repr__(self) -> str:
        return f"F({self.field_name!r})"


class FExpression:
    """Expression involving F objects and operators."""

    def __init__(self, left: F | FExpression | Any, op: str, right: Any) -> None:
        self.left = left
        self.op = op
        self.right = right

    def resolve(self, model_class: type) -> ColumnElement[Any]:
        """Resolve to SQLAlchemy expression."""
        left_col = self.left.resolve(model_class) if isinstance(self.left, (F, FExpression)) else self.left
        right_col = self.right.resolve(model_class) if isinstance(self.right, (F, FExpression)) else self.right

        if self.op == "+":
            return left_col + right_col
        elif self.op == "-":
            return left_col - right_col
        elif self.op == "*":
            return left_col * right_col
        elif self.op == "/":
            return left_col / right_col
        else:
            raise ValueError(f"Unknown operator: {self.op}")

    def __repr__(self) -> str:
        return f"({self.left} {self.op} {self.right})"


def resolve_value(value: Any, model_class: type) -> Any:
    """Resolve an ``F()``/``FExpression`` value to a SQLAlchemy column
    expression for the given model; pass any other value through unchanged.

    Used wherever a filter/lookup value might be a field reference instead
    of a literal, e.g. ``.filter(karma__gt=F("num_posts"))``.
    """
    if isinstance(value, (F, FExpression)):
        return value.resolve(model_class)
    return value


_LOOKUPS = frozenset(
    {
        "exact",
        "iexact",
        "contains",
        "icontains",
        "gt",
        "gte",
        "lt",
        "lte",
        "in",
        "isnull",
        "startswith",
        "istartswith",
        "endswith",
        "iendswith",
    }
)


def lookup_expr(model_class: type, key: str, value: Any) -> ColumnElement[bool]:
    """Turn ``name__icontains`` or ``author__name__icontains`` into a SQL expression.

    A path walks relationships. ``author__name`` filters the related ``name``
    column. The last segment is a lookup when it is one of the names
    ``_apply_lookup`` understands. Otherwise the comparison is equality.
    """
    parts = key.split("__")
    lookup = "exact"
    if len(parts) > 1 and parts[-1] in _LOOKUPS:
        lookup = parts[-1]
        parts = parts[:-1]
    return _path_expr(model_class, parts, lookup, value)


def _path_expr(model_class: type, parts: list[str], lookup: str, value: Any) -> ColumnElement[bool]:
    from sqlalchemy.orm import RelationshipProperty

    if not parts:
        raise ValueError("Empty filter path")
    name, *rest = parts
    attr = getattr(model_class, name)
    prop = getattr(attr, "property", None)
    if isinstance(prop, RelationshipProperty):
        if not rest:
            raise ValueError(f"Filter {name!r} needs a field on the related model")
        target = prop.mapper.class_
        inner = _path_expr(target, rest, lookup, value)
        if prop.uselist:
            return attr.any(inner)
        return attr.has(inner)
    if rest:
        raise ValueError(f"Unknown lookup path: {'__'.join(parts)}")
    return _apply_lookup(attr, lookup, value)


def _apply_lookup(column: ColumnElement[Any], lookup: str, value: Any) -> ColumnElement[bool]:
    """Apply a field lookup to a column.

    Supported lookups:
        - exact: field == value (default)
        - iexact: case-insensitive exact match
        - contains: field.contains(value)
        - icontains: case-insensitive contains
        - gt, gte, lt, lte: comparisons
        - in: field.in_(value)
        - isnull: field.is_(None) or field.isnot(None)
        - startswith, istartswith, endswith, iendswith: string matching
    """
    if lookup == "exact":
        return column == value
    elif lookup == "iexact":
        return column.ilike(value)
    elif lookup == "contains":
        return column.contains(value)
    elif lookup == "icontains":
        return column.ilike(f"%{value}%")
    elif lookup == "gt":
        return column > value
    elif lookup == "gte":
        return column >= value
    elif lookup == "lt":
        return column < value
    elif lookup == "lte":
        return column <= value
    elif lookup == "in":
        return column.in_(value)
    elif lookup == "isnull":
        return column.is_(None) if value else column.isnot(None)
    elif lookup == "startswith":
        return column.like(f"{value}%")
    elif lookup == "istartswith":
        return column.ilike(f"{value}%")
    elif lookup == "endswith":
        return column.like(f"%{value}")
    elif lookup == "iendswith":
        return column.ilike(f"%{value}")
    else:
        raise ValueError(f"Unknown lookup: {lookup}")


__all__ = ["F", "FExpression", "Q", "lookup_expr", "resolve_value"]
