"""Tests for QuerySet enhancements (field lookups, Q/F objects)."""

from __future__ import annotations

import pytest

from fastframe.models import F, Q
from fastframe.models.query import _apply_lookup


def test_q_object_creation():
    """Q object stores conditions."""
    q = Q(name="Alice", age=25)
    assert q.conditions == {"name": "Alice", "age": 25}
    assert q.connector == "AND"
    assert q.negated is False


def test_q_object_and():
    """Q object AND combination."""
    q1 = Q(name="Alice")
    q2 = Q(age=25)
    combined = q1 & q2

    assert combined.connector == "AND"
    assert len(combined.children) == 2


def test_q_object_or():
    """Q object OR combination."""
    q1 = Q(name="Alice")
    q2 = Q(name="Bob")
    combined = q1 | q2

    assert combined.connector == "OR"
    assert len(combined.children) == 2


def test_q_object_not():
    """Q object NOT negation."""
    q = Q(published=True)
    negated = ~q

    assert negated.negated is True
    assert negated.conditions == {"published": True}


def test_q_object_complex():
    """Q object complex combinations."""
    # (published=True AND featured=True) OR author="Alice"
    q = (Q(published=True, featured=True) | Q(author="Alice"))

    assert q.connector == "OR"
    assert len(q.children) == 2
    assert q.children[0].conditions == {"published": True, "featured": True}
    assert q.children[1].conditions == {"author": "Alice"}


def test_f_object_creation():
    """F object stores field name."""
    f = F("karma")
    assert f.field_name == "karma"


def test_f_object_addition():
    """F object arithmetic: addition."""
    f = F("karma") + 1
    assert f.left.field_name == "karma"
    assert f.op == "+"
    assert f.right == 1


def test_f_object_subtraction():
    """F object arithmetic: subtraction."""
    f = F("count") - 5
    assert f.left.field_name == "count"
    assert f.op == "-"
    assert f.right == 5


def test_f_object_multiplication():
    """F object arithmetic: multiplication."""
    f = F("price") * 2
    assert f.op == "*"


def test_f_object_division():
    """F object arithmetic: division."""
    f = F("total") / 10
    assert f.op == "/"


def test_apply_lookup_gt():
    """_apply_lookup handles __gt."""
    from sqlalchemy import Column, Integer

    col = Column("age", Integer)
    expr = _apply_lookup(col, "gt", 18)
    assert ">" in str(expr)


def test_apply_lookup_gte():
    """_apply_lookup handles __gte."""
    from sqlalchemy import Column, Integer

    col = Column("age", Integer)
    expr = _apply_lookup(col, "gte", 18)
    assert ">=" in str(expr)


def test_apply_lookup_lt():
    """_apply_lookup handles __lt."""
    from sqlalchemy import Column, Integer

    col = Column("score", Integer)
    expr = _apply_lookup(col, "lt", 100)
    assert "<" in str(expr)


def test_apply_lookup_lte():
    """_apply_lookup handles __lte."""
    from sqlalchemy import Column, Integer

    col = Column("score", Integer)
    expr = _apply_lookup(col, "lte", 100)
    assert "<=" in str(expr)


def test_apply_lookup_icontains():
    """_apply_lookup handles __icontains."""
    from sqlalchemy import Column, String

    col = Column("name", String)
    expr = _apply_lookup(col, "icontains", "python")
    # Should generate LIKE with wildcards
    assert "ilike" in str(expr).lower() or "like" in str(expr).lower()


def test_apply_lookup_in():
    """_apply_lookup handles __in."""
    from sqlalchemy import Column, String

    col = Column("status", String)
    expr = _apply_lookup(col, "in", ["draft", "published"])
    expr_str = str(expr).lower()
    assert "in" in expr_str


def test_apply_lookup_isnull():
    """_apply_lookup handles __isnull."""
    from sqlalchemy import Column, String

    col = Column("deleted_at", String)

    # isnull=True → IS NULL
    expr_null = _apply_lookup(col, "isnull", True)
    assert "is" in str(expr_null).lower() or "none" in str(expr_null).lower()

    # isnull=False → IS NOT NULL
    expr_not_null = _apply_lookup(col, "isnull", False)
    assert "not" in str(expr_not_null).lower() or "is" in str(expr_not_null).lower()


def test_apply_lookup_startswith():
    """_apply_lookup handles __startswith."""
    from sqlalchemy import Column, String

    col = Column("email", String)
    expr = _apply_lookup(col, "startswith", "admin")
    assert "like" in str(expr).lower()


def test_apply_lookup_endswith():
    """_apply_lookup handles __endswith."""
    from sqlalchemy import Column, String

    col = Column("filename", String)
    expr = _apply_lookup(col, "endswith", ".pdf")
    assert "like" in str(expr).lower()


def test_apply_lookup_unknown():
    """_apply_lookup raises error for unknown lookup."""
    from sqlalchemy import Column, String

    col = Column("name", String)

    with pytest.raises(ValueError, match="Unknown lookup"):
        _apply_lookup(col, "invalid_lookup", "value")


def test_q_repr():
    """Q object has readable repr."""
    q = Q(name="Alice", age=25)
    repr_str = repr(q)
    assert "Q(" in repr_str
    assert "name" in repr_str


def test_f_repr():
    """F object has readable repr."""
    f = F("karma")
    assert "F('karma')" in repr(f)
