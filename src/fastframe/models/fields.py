"""Django-style declarative fields for FastFrame models.

Provides a clean, ergonomic API for defining model fields while compiling to
SQLAlchemy underneath. Admin auto-generates forms by introspecting field
metadata.

Example:
    from fastframe.models import Model, fields

    class Book(Model):
        title = fields.CharField(max_length=200)
        published = fields.DateField()
        is_active = fields.BooleanField(default=True)

This compiles to SQLAlchemy mapped_column() behind the scenes, so migrations
work unchanged. The old mapped_column() syntax still works for escape hatches.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

if TYPE_CHECKING:
    from sqlalchemy.sql import ColumnElement

# Sentinel for "no default provided"
NOT_PROVIDED = object()


class Field:
    """Base class for all model fields.

    Fields are descriptors that compile to SQLAlchemy mapped_column() when a
    model class is created. They store metadata for validation and admin form
    generation.
    """

    # Default SQLAlchemy type (subclasses override)
    _sqlalchemy_type = None

    def __init__(
        self,
        *,
        primary_key: bool = False,
        unique: bool = False,
        null: bool = False,
        blank: bool = False,
        default: Any = NOT_PROVIDED,
        db_default: Any = None,
        choices: list[tuple[Any, str]] | None = None,
        help_text: str = "",
        verbose_name: str | None = None,
        validators: list[Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a field.

        Args:
            primary_key: Make this field the primary key.
            unique: Add a unique constraint.
            null: Allow NULL in database (default False).
            blank: Allow empty values in forms (not enforced at DB level).
            default: Python-level default value.
            db_default: Server-side default (SQL expression).
            choices: List of (value, display_name) tuples for validation/admin.
            help_text: Help text for admin forms.
            verbose_name: Human-readable name (defaults to field name).
            validators: List of validator callables.
            **kwargs: Additional SQLAlchemy column kwargs.
        """
        self.primary_key = primary_key
        self.unique = unique
        self.null = null
        self.blank = blank
        self.default = default
        self.db_default = db_default
        self.choices = choices
        self.help_text = help_text
        self.verbose_name = verbose_name
        self.validators = validators or []
        self.extra_kwargs = kwargs

        # Set by ModelMeta when model class is created
        self.name: str | None = None
        self.model_class: type | None = None

    def __set_name__(self, owner: type, name: str) -> None:
        """Called when field is assigned to a class attribute."""
        self.name = name
        if self.verbose_name is None:
            # Convert "field_name" → "Field Name"
            self.verbose_name = name.replace("_", " ").title()

    def get_sqlalchemy_type(self) -> Any:
        """Return the SQLAlchemy type class for this field.

        Subclasses override this to provide specific types (e.g. String(200)).
        """
        if self._sqlalchemy_type is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must define _sqlalchemy_type "
                f"or override get_sqlalchemy_type()"
            )
        return self._sqlalchemy_type

    def to_sqlalchemy_column(self) -> ColumnElement[Any]:
        """Convert this field to a SQLAlchemy mapped_column().

        Returns a mapped_column() that Alembic can introspect for migrations.
        """
        col_type = self.get_sqlalchemy_type()
        kwargs = {
            "primary_key": self.primary_key,
            "unique": self.unique,
            "nullable": self.null,
            **self.extra_kwargs,
        }

        # Add default if provided
        if self.default is not NOT_PROVIDED:
            kwargs["default"] = self.default

        # Add server default if provided
        if self.db_default is not None:
            kwargs["server_default"] = self.db_default

        return mapped_column(col_type, **kwargs)

    def get_type_annotation(self) -> type:
        """Return the Mapped[...] type annotation for this field.

        Used by ModelMeta to set __annotations__ on the model class.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement get_type_annotation()"
        )

    def validate(self, value: Any) -> None:
        """Validate a value for this field.

        Called by Model.full_clean() or admin forms before saving.
        Raises ValidationError if invalid.
        """
        # Blank check (for forms, not DB)
        if not self.blank and value in (None, ""):
            from fastframe.models.exceptions import ValidationError

            raise ValidationError(f"{self.verbose_name} cannot be blank.")

        # Choices validation
        if self.choices and value not in [choice[0] for choice in self.choices]:
            from fastframe.models.exceptions import ValidationError

            raise ValidationError(
                f"{self.verbose_name} must be one of: {[c[0] for c in self.choices]}"
            )

        # Custom validators
        for validator in self.validators:
            validator(value)


# --- Concrete Field Types ---


class AutoField(Field):
    """Auto-incrementing integer primary key."""

    def __init__(self, **kwargs: Any) -> None:
        kwargs.setdefault("primary_key", True)
        super().__init__(**kwargs)

    def get_sqlalchemy_type(self) -> Any:
        return Integer

    def get_type_annotation(self) -> type:
        return Mapped[int]

    def to_sqlalchemy_column(self) -> ColumnElement[Any]:
        # AutoField always has autoincrement=True
        self.extra_kwargs.setdefault("autoincrement", True)
        return super().to_sqlalchemy_column()


class BigAutoField(AutoField):
    """Auto-incrementing big integer primary key."""

    def get_sqlalchemy_type(self) -> Any:
        return BigInteger


class CharField(Field):
    """Variable-length string field with max_length."""

    def __init__(self, max_length: int, **kwargs: Any) -> None:
        if max_length is None or max_length <= 0:
            raise ValueError("CharField requires max_length > 0")
        self.max_length = max_length
        super().__init__(**kwargs)

    def get_sqlalchemy_type(self) -> Any:
        return String(self.max_length)

    def get_type_annotation(self) -> type:
        return Mapped[str]

    def validate(self, value: Any) -> None:
        super().validate(value)
        if value and len(str(value)) > self.max_length:
            from fastframe.models.exceptions import ValidationError

            raise ValidationError(
                f"{self.verbose_name} cannot exceed {self.max_length} characters."
            )


class TextField(Field):
    """Unlimited-length text field."""

    _sqlalchemy_type = Text

    def get_type_annotation(self) -> type:
        return Mapped[str]


class IntegerField(Field):
    """Integer field."""

    _sqlalchemy_type = Integer

    def get_type_annotation(self) -> type:
        return Mapped[int]


class BigIntegerField(Field):
    """Big integer field (64-bit)."""

    _sqlalchemy_type = BigInteger

    def get_type_annotation(self) -> type:
        return Mapped[int]


class BooleanField(Field):
    """Boolean field (True/False, never NULL by default)."""

    _sqlalchemy_type = Boolean

    def __init__(self, **kwargs: Any) -> None:
        # Booleans should default to False if no default specified
        if "default" not in kwargs:
            kwargs["default"] = False
        # Booleans are never nullable by default
        kwargs.setdefault("null", False)
        super().__init__(**kwargs)

    def get_type_annotation(self) -> type:
        return Mapped[bool]


class FloatField(Field):
    """Floating-point number field."""

    _sqlalchemy_type = Float

    def get_type_annotation(self) -> type:
        return Mapped[float]


class DateField(Field):
    """Date field (no time component)."""

    _sqlalchemy_type = Date

    def get_type_annotation(self) -> type:
        return Mapped[date]


class DateTimeField(Field):
    """DateTime field with optional auto_now/auto_now_add."""

    _sqlalchemy_type = DateTime

    def __init__(
        self,
        *,
        auto_now: bool = False,
        auto_now_add: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize DateTimeField.

        Args:
            auto_now: Automatically set to now on every save (like updated_at).
            auto_now_add: Set to now on creation only (like created_at).
            **kwargs: Additional field options.
        """
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add

        # auto_now_add sets server default to current timestamp
        if auto_now_add:
            from sqlalchemy.sql import func

            kwargs.setdefault("db_default", func.now())

        super().__init__(**kwargs)

    def get_type_annotation(self) -> type:
        return Mapped[datetime]


# Alias for convenience
SmallIntegerField = IntegerField  # SQLAlchemy doesn't distinguish by default


__all__ = [
    "Field",
    "AutoField",
    "BigAutoField",
    "CharField",
    "TextField",
    "IntegerField",
    "BigIntegerField",
    "SmallIntegerField",
    "BooleanField",
    "FloatField",
    "DateField",
    "DateTimeField",
]
