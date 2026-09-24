"""Tests for additional field types."""

from __future__ import annotations

import pytest
from sqlalchemy import inspect

from fastframe.models import Model, ValidationError, fields


def test_decimalfield():
    """DecimalField creates Numeric column."""

    class Product(Model):
        __tablename__ = "products_decimal"
        price = fields.DecimalField(max_digits=10, decimal_places=2)

    mapper = inspect(Product)
    price_col = mapper.columns["price"]
    assert str(price_col.type) == "NUMERIC(10, 2)"
    assert Product.__annotations__["price"]


def test_decimalfield_validation():
    """DecimalField validates max_digits and decimal_places."""
    with pytest.raises(ValueError, match="max_digits must be > 0"):
        fields.DecimalField(max_digits=0, decimal_places=2)

    with pytest.raises(ValueError, match="decimal_places must be >= 0"):
        fields.DecimalField(max_digits=10, decimal_places=-1)

    with pytest.raises(ValueError, match="cannot exceed max_digits"):
        fields.DecimalField(max_digits=5, decimal_places=10)


def test_emailfield():
    """EmailField validates email addresses."""

    class User(Model):
        __tablename__ = "users_email"
        email = fields.EmailField()

    field = User._meta["fields"]["email"]

    # Valid emails
    field.validate("user@example.com")
    field.validate("user.name+tag@example.co.uk")

    # Invalid emails
    with pytest.raises(ValidationError, match="valid email"):
        field.validate("not-an-email")

    with pytest.raises(ValidationError, match="valid email"):
        field.validate("@example.com")


def test_emailfield_max_length():
    """EmailField has default max_length of 254."""

    class User(Model):
        __tablename__ = "users_email_len"
        email = fields.EmailField()

    field = User._meta["fields"]["email"]
    assert field.max_length == 254


def test_urlfield():
    """URLField validates URLs."""

    class Link(Model):
        __tablename__ = "links"
        url = fields.URLField()

    field = Link._meta["fields"]["url"]

    # Valid URLs
    field.validate("https://example.com")
    field.validate("http://localhost:8000/path")
    field.validate("https://sub.domain.com/path?query=1")

    # Invalid URLs
    with pytest.raises(ValidationError, match="valid URL"):
        field.validate("not-a-url")

    with pytest.raises(ValidationError, match="valid URL"):
        field.validate("ftp://example.com")  # only http/https


def test_uuidfield():
    """UUIDField creates UUID column with auto-generation."""

    class Session(Model):
        __tablename__ = "sessions_uuid"
        session_id = fields.UUIDField(primary_key=True)

    mapper = inspect(Session)
    session_id_col = mapper.columns["session_id"]
    assert "UUID" in str(session_id_col.type)

    # Check auto-generation (UUID7, not UUID4)
    field = Session._meta["fields"]["session_id"]
    assert field.default is not None
    assert callable(field.default)
    # UUID7 is either built-in (Python 3.14+) or from uuid-utils
    # Just verify it generates valid UUIDs
    generated = field.default()
    assert len(str(generated)) == 36  # UUID string format


def test_jsonfield():
    """JSONField creates JSON column."""

    class Config(Model):
        __tablename__ = "configs_json"
        settings = fields.JSONField()

    mapper = inspect(Config)
    settings_col = mapper.columns["settings"]
    # SQLAlchemy adapts JSON type based on backend
    assert "JSON" in str(settings_col.type)


def test_foreignkey_basic():
    """ForeignKey creates foreign key constraint."""

    class Author(Model):
        __tablename__ = "authors_fk"
        name = fields.CharField(max_length=100)

    class Book(Model):
        __tablename__ = "books_fk"
        title = fields.CharField(max_length=200)
        author_id = fields.ForeignKey("Author", on_delete="CASCADE")

    mapper = inspect(Book)
    author_id_col = mapper.columns["author_id"]

    # Check foreign key constraint exists
    fks = list(author_id_col.foreign_keys)
    assert len(fks) == 1
    # FK target will be "authors.id" (pluralized model name)
    assert ".id" in str(fks[0].target_fullname)


def test_foreignkey_on_delete_validation():
    """ForeignKey validates on_delete options."""
    with pytest.raises(ValueError, match="on_delete must be"):
        fields.ForeignKey("User", on_delete="INVALID")

    with pytest.raises(ValueError, match="requires null=True"):
        fields.ForeignKey("User", on_delete="SET_NULL", null=False)


def test_foreignkey_nullable_by_default():
    """ForeignKey is nullable by default."""

    class Post(Model):
        __tablename__ = "posts_fk_null"
        author_id = fields.ForeignKey("User")

    field = Post._meta["fields"]["author_id"]
    assert field.null is True


def test_foreignkey_related_name():
    """ForeignKey stores related_name for reverse relationships."""

    class User(Model):
        __tablename__ = "users_fk_related"
        name = fields.CharField(max_length=100)

    class Post(Model):
        __tablename__ = "posts_fk_related"
        author_id = fields.ForeignKey("User", related_name="posts")

    field = Post._meta["fields"]["author_id"]
    assert field.related_name == "posts"


def test_mixed_field_types():
    """Can mix different field types in one model."""

    class ComplexModel(Model):
        __tablename__ = "complex_model"
        name = fields.CharField(max_length=100)
        email = fields.EmailField()
        price = fields.DecimalField(max_digits=10, decimal_places=2)
        settings = fields.JSONField()
        session_id = fields.UUIDField()
        is_active = fields.BooleanField()

    assert len(ComplexModel._meta["fields"]) == 7  # +id auto-added
