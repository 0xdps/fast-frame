"""Tests for Django-style Field API."""

from __future__ import annotations

from datetime import date, datetime

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import Mapped, mapped_column

from fastframe.models import Model, ValidationError, fields


def test_charfield_basic():
    """CharField with max_length creates String column."""

    class Book(Model):
        __tablename__ = "books"
        title = fields.CharField(max_length=200)

    assert hasattr(Book, "title")
    assert "title" in Book.__annotations__
    assert Book.__annotations__["title"] == Mapped[str]

    # Introspect SQLAlchemy column
    mapper = inspect(Book)
    title_col = mapper.columns["title"]
    assert title_col.type.length == 200
    assert title_col.nullable is False  # default


def test_charfield_requires_max_length():
    """CharField must specify max_length."""
    with pytest.raises(ValueError, match="requires max_length"):
        fields.CharField(max_length=None)


def test_textfield():
    """TextField creates unlimited Text column."""

    class PostContent(Model):
        __tablename__ = "post_content"
        content = fields.TextField()

    mapper = inspect(PostContent)
    content_col = mapper.columns["content"]
    assert str(content_col.type) == "TEXT"


def test_integerfield():
    """IntegerField creates Integer column."""

    class Counter(Model):
        __tablename__ = "counters"
        value = fields.IntegerField(default=0)

    mapper = inspect(Counter)
    value_col = mapper.columns["value"]
    assert str(value_col.type) == "INTEGER"
    assert value_col.default.arg == 0


def test_booleanfield_defaults_false():
    """BooleanField defaults to False if no default specified."""

    class Feature(Model):
        __tablename__ = "features"
        enabled = fields.BooleanField()

    mapper = inspect(Feature)
    enabled_col = mapper.columns["enabled"]
    assert str(enabled_col.type) == "BOOLEAN"
    assert enabled_col.nullable is False
    
    # Check field metadata has the default
    field_meta = Feature._meta["fields"]["enabled"]
    assert field_meta.default is False


def test_booleanfield_custom_default():
    """BooleanField can have custom default."""

    class Setting(Model):
        __tablename__ = "settings"
        is_active = fields.BooleanField(default=True)

    mapper = inspect(Setting)
    is_active_col = mapper.columns["is_active"]
    assert is_active_col.default.arg is True


def test_datefield():
    """DateField creates Date column."""

    class Event(Model):
        __tablename__ = "events"
        event_date = fields.DateField()

    assert Event.__annotations__["event_date"] == Mapped[date]


def test_datetimefield():
    """DateTimeField creates DateTime column."""

    class Log(Model):
        __tablename__ = "logs"
        created_at = fields.DateTimeField()

    assert Log.__annotations__["created_at"] == Mapped[datetime]


def test_datetimefield_auto_now_add():
    """DateTimeField with auto_now_add sets server default."""

    class Article(Model):
        __tablename__ = "articles"
        created_at = fields.DateTimeField(auto_now_add=True)

    mapper = inspect(Article)
    created_col = mapper.columns["created_at"]
    assert created_col.server_default is not None


def test_auto_primary_key():
    """Model auto-adds 'id' primary key if not specified."""

    class Foo(Model):
        __tablename__ = "foos"
        name = fields.CharField(max_length=100)

    # Should have auto-generated id field
    assert "id" in Foo._meta["fields"]
    mapper = inspect(Foo)
    id_col = mapper.columns["id"]
    assert id_col.primary_key is True
    assert id_col.autoincrement is True


def test_explicit_primary_key():
    """Model respects explicit primary_key field."""

    class UserAccount(Model):
        __tablename__ = "user_accounts"
        email = fields.CharField(max_length=255, primary_key=True)

    # Should NOT auto-add id
    assert "id" not in UserAccount._meta["fields"]
    mapper = inspect(UserAccount)
    assert mapper.primary_key[0].name == "email"


def test_meta_db_table():
    """Meta.db_table sets __tablename__."""

    class Product(Model):
        name = fields.CharField(max_length=100)

        class Meta:
            db_table = "products"

    assert Product.__tablename__ == "products"


def test_meta_verbose_name():
    """Meta.verbose_name stored in _meta."""

    class BlogPost(Model):
        __tablename__ = "blog_posts"
        title = fields.CharField(max_length=200)

        class Meta:
            verbose_name = "Blog Post"
            verbose_name_plural = "Blog Posts"

    assert BlogPost._meta["verbose_name"] == "Blog Post"
    assert BlogPost._meta["verbose_name_plural"] == "Blog Posts"


def test_meta_ordering():
    """Meta.ordering stored in _meta."""

    class Comment(Model):
        __tablename__ = "comments"
        created_at = fields.DateTimeField()

        class Meta:
            ordering = ["-created_at"]

    assert Comment._meta["ordering"] == ["-created_at"]


def test_field_unique():
    """Field unique=True creates unique constraint."""

    class Username(Model):
        __tablename__ = "usernames"
        name = fields.CharField(max_length=100, unique=True)

    mapper = inspect(Username)
    name_col = mapper.columns["name"]
    assert name_col.unique is True


def test_field_null():
    """Field null=True allows NULL values."""

    class OptionalField(Model):
        __tablename__ = "optional_fields"
        optional = fields.CharField(max_length=100, null=True)

    mapper = inspect(OptionalField)
    optional_col = mapper.columns["optional"]
    assert optional_col.nullable is True


def test_field_verbose_name_auto():
    """Field auto-generates verbose_name from field name."""

    class ExampleVerbose1(Model):
        __tablename__ = "example_verbose_1"
        first_name = fields.CharField(max_length=100)

    field_meta = ExampleVerbose1._meta["fields"]["first_name"]
    assert field_meta.verbose_name == "First Name"


def test_field_verbose_name_explicit():
    """Field respects explicit verbose_name."""

    class ExampleVerbose2(Model):
        __tablename__ = "example_verbose_2"
        first_name = fields.CharField(max_length=100, verbose_name="Given Name")

    field_meta = ExampleVerbose2._meta["fields"]["first_name"]
    assert field_meta.verbose_name == "Given Name"


def test_field_choices():
    """Field stores choices for validation."""

    class Status(Model):
        __tablename__ = "statuses"
        status = fields.CharField(
            max_length=20,
            choices=[
                ("draft", "Draft"),
                ("published", "Published"),
            ],
        )

    field_meta = Status._meta["fields"]["status"]
    assert field_meta.choices == [("draft", "Draft"), ("published", "Published")]


def test_field_help_text():
    """Field stores help_text for forms."""

    class ExampleHelp(Model):
        __tablename__ = "example_help"
        email = fields.CharField(max_length=255, help_text="Enter a valid email")

    field_meta = ExampleHelp._meta["fields"]["email"]
    assert field_meta.help_text == "Enter a valid email"


def test_backward_compat_mapped_column():
    """Old mapped_column syntax still works."""

    class Legacy(Model):
        __tablename__ = "legacy"
        # Old v0.1/v0.2 style
        name: Mapped[str] = mapped_column()

    assert hasattr(Legacy, "name")


def test_mixed_syntax():
    """Can mix new field API with old mapped_column."""

    class Mixed(Model):
        __tablename__ = "mixed"
        # New style
        title = fields.CharField(max_length=200)
        # Old style
        legacy: Mapped[str] = mapped_column()

    assert hasattr(Mixed, "title")
    assert hasattr(Mixed, "legacy")


def test_bigautofield():
    """BigAutoField creates BigInteger primary key."""

    class BigModel(Model):
        __tablename__ = "big_models"
        id = fields.BigAutoField(primary_key=True)
        name = fields.CharField(max_length=100)

    mapper = inspect(BigModel)
    id_col = mapper.columns["id"]
    assert str(id_col.type) == "BIGINT"
    assert id_col.primary_key is True


def test_bigintegerfield():
    """BigIntegerField creates BigInteger column."""

    class LargeNumbers(Model):
        __tablename__ = "large_numbers"
        big_value = fields.BigIntegerField()

    mapper = inspect(LargeNumbers)
    big_value_col = mapper.columns["big_value"]
    assert str(big_value_col.type) == "BIGINT"


def test_floatfield():
    """FloatField creates Float column."""

    class Measurement(Model):
        __tablename__ = "measurements"
        value = fields.FloatField()

    mapper = inspect(Measurement)
    value_col = mapper.columns["value"]
    assert "FLOAT" in str(value_col.type) or "REAL" in str(value_col.type)


def test_charfield_validation_max_length():
    """CharField.validate() checks max_length."""

    class ExampleValidation1(Model):
        __tablename__ = "example_validation_1"
        name = fields.CharField(max_length=10)

    field = ExampleValidation1._meta["fields"]["name"]

    # Valid
    field.validate("short")

    # Too long
    with pytest.raises(ValidationError, match="cannot exceed 10 characters"):
        field.validate("this is way too long")


def test_field_validation_blank():
    """Field.validate() checks blank constraint."""

    class ExampleValidation2(Model):
        __tablename__ = "example_validation_2"
        required = fields.CharField(max_length=100, blank=False)

    field = ExampleValidation2._meta["fields"]["required"]

    # Valid
    field.validate("value")

    # Empty
    with pytest.raises(ValidationError, match="cannot be blank"):
        field.validate("")


def test_field_validation_choices():
    """Field.validate() checks choices constraint."""

    class ExampleValidation3(Model):
        __tablename__ = "example_validation_3"
        status = fields.CharField(
            max_length=20,
            choices=[("draft", "Draft"), ("published", "Published")],
        )

    field = ExampleValidation3._meta["fields"]["status"]

    # Valid
    field.validate("draft")

    # Invalid choice
    with pytest.raises(ValidationError, match="must be one of"):
        field.validate("invalid")


def test_meta_fields_introspection():
    """_meta['fields'] contains all Field instances."""

    class BookIntro(Model):
        __tablename__ = "book_intro"
        title = fields.CharField(max_length=200)
        published = fields.DateField()
        is_active = fields.BooleanField()

    meta_fields = BookIntro._meta["fields"]
    assert "id" in meta_fields  # auto-added
    assert "title" in meta_fields
    assert "published" in meta_fields
    assert "is_active" in meta_fields

    # Fields should be Field instances
    assert isinstance(meta_fields["title"], fields.CharField)
    assert isinstance(meta_fields["published"], fields.DateField)
    assert isinstance(meta_fields["is_active"], fields.BooleanField)


def test_field_extra_kwargs():
    """Field can accept extra SQLAlchemy kwargs."""

    class ExampleKwargs(Model):
        __tablename__ = "example_kwargs"
        indexed = fields.CharField(max_length=100, index=True)

    mapper = inspect(ExampleKwargs)
    indexed_col = mapper.columns["indexed"]
    assert indexed_col.index is True
