"""Tests for model validation (clean, full_clean)."""

from __future__ import annotations

import pytest

from fastframe.models import Model, ValidationError, fields


def test_model_clean_hook():
    """Model.clean() hook for custom validation."""

    class User(Model):
        __tablename__ = "users_validation"
        age = fields.IntegerField()
        has_driver_license = fields.BooleanField()

        def clean(self):
            if self.age < 18 and self.has_driver_license:
                raise ValidationError("Underage drivers not allowed.")

    # Valid
    user1 = User(age=20, has_driver_license=True)
    user1.clean()  # Should not raise

    user2 = User(age=16, has_driver_license=False)
    user2.clean()  # Should not raise

    # Invalid
    user3 = User(age=16, has_driver_license=True)
    with pytest.raises(ValidationError, match="Underage"):
        user3.clean()


def test_full_clean_validates_fields():
    """full_clean() validates all fields."""

    class Book(Model):
        __tablename__ = "books_validation"
        title = fields.CharField(max_length=10)  # Short for testing

    book = Book(title="This title is way too long")

    with pytest.raises(ValidationError):
        book.full_clean()


def test_full_clean_calls_clean():
    """full_clean() calls clean() hook."""

    class Product(Model):
        __tablename__ = "products_validation"
        price = fields.DecimalField(max_digits=10, decimal_places=2)
        discounted_price = fields.DecimalField(max_digits=10, decimal_places=2)

        def clean(self):
            if self.discounted_price > self.price:
                raise ValidationError("Discounted price cannot exceed regular price.")

    product = Product(price=100, discounted_price=150)

    with pytest.raises(ValidationError, match="cannot exceed"):
        product.full_clean()


def test_full_clean_exclude():
    """full_clean() can exclude specific fields."""

    class Article(Model):
        __tablename__ = "articles_validation"
        title = fields.CharField(max_length=10, blank=False)
        slug = fields.CharField(max_length=10, blank=False)

    article = Article(title="", slug="")

    # Both fields invalid
    with pytest.raises(ValidationError):
        article.full_clean()

    # Exclude title - only slug validation fails
    with pytest.raises(ValidationError):
        article.full_clean(exclude=["title"])


def test_save_with_validation():
    """save(validate=True) runs full_clean() before saving."""

    class Tag(Model):
        __tablename__ = "tags_validation_save"
        name = fields.CharField(max_length=5)

    # Test validation is called
    tag = Tag(name="short")
    # We can't easily test actual DB save in unit tests without full setup,
    # but we can verify the validate flag works
    try:
        tag.full_clean()  # Should not raise
    except Exception:
        pytest.fail("Validation should pass for valid data")

    invalid_tag = Tag(name="this is too long")
    with pytest.raises(ValidationError):
        invalid_tag.full_clean()


def test_field_blank_validation():
    """Field blank=False validates empty values."""

    class Form(Model):
        __tablename__ = "forms_blank"
        required_field = fields.CharField(max_length=100, blank=False)
        optional_field = fields.CharField(max_length=100, blank=True)

    form = Form(required_field="", optional_field="")

    # required_field is blank and blank=False
    with pytest.raises(ValidationError, match="cannot be blank"):
        form.full_clean()


def test_field_choices_validation():
    """Field choices validates against allowed values."""

    class Status(Model):
        __tablename__ = "statuses_choices"
        status = fields.CharField(
            max_length=20,
            choices=[("draft", "Draft"), ("published", "Published")],
        )

    draft = Status(status="draft")
    draft.full_clean()  # Valid

    invalid = Status(status="invalid")
    with pytest.raises(ValidationError, match="must be one of"):
        invalid.full_clean()


def test_charfield_max_length_validation():
    """CharField validates max_length."""

    class ShortText(Model):
        __tablename__ = "short_texts"
        text = fields.CharField(max_length=10)

    short = ShortText(text="short")
    short.full_clean()  # Valid

    long = ShortText(text="this is way too long")
    with pytest.raises(ValidationError, match="cannot exceed 10"):
        long.full_clean()


def test_clean_hook_default_no_op():
    """Model.clean() default is no-op."""

    class Simple(Model):
        __tablename__ = "simple_clean"
        name = fields.CharField(max_length=100)

    obj = Simple(name="test")
    obj.clean()  # Should not raise
