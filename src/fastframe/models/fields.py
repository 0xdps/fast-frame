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

import re
import uuid as uuid_module
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    UUID,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Integer,
    Numeric,
    String,
    Text,
)
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
        write_only: bool = False,
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
            write_only: Accept the value on write, but omit it from admin API responses.
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
        self.write_only = write_only
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


class DecimalField(Field):
    """Fixed-precision decimal field for money, percentages, etc."""

    def __init__(
        self,
        *,
        max_digits: int,
        decimal_places: int,
        **kwargs: Any,
    ) -> None:
        """Initialize DecimalField.

        Args:
            max_digits: Total number of digits (precision).
            decimal_places: Number of digits after decimal point (scale).
            **kwargs: Additional field options.
        """
        if max_digits <= 0 or decimal_places < 0:
            raise ValueError(
                "max_digits must be > 0 and decimal_places must be >= 0"
            )
        if decimal_places > max_digits:
            raise ValueError("decimal_places cannot exceed max_digits")

        self.max_digits = max_digits
        self.decimal_places = decimal_places
        super().__init__(**kwargs)

    def get_sqlalchemy_type(self) -> Any:
        return Numeric(precision=self.max_digits, scale=self.decimal_places)

    def get_type_annotation(self) -> type:
        return Mapped[Decimal]


class EmailField(CharField):
    """Email address field with validation."""

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __init__(self, max_length: int = 254, **kwargs: Any) -> None:
        """Initialize EmailField.

        Args:
            max_length: Maximum length (default 254 per RFC 5321).
            **kwargs: Additional field options.
        """
        super().__init__(max_length=max_length, **kwargs)

    def validate(self, value: Any) -> None:
        super().validate(value)
        if value and not self.EMAIL_REGEX.match(str(value)):
            from fastframe.models.exceptions import ValidationError

            raise ValidationError(f"{self.verbose_name} must be a valid email address.")


class URLField(CharField):
    """URL field with validation."""

    URL_REGEX = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    def __init__(self, max_length: int = 200, **kwargs: Any) -> None:
        """Initialize URLField.

        Args:
            max_length: Maximum length (default 200).
            **kwargs: Additional field options.
        """
        super().__init__(max_length=max_length, **kwargs)

    def validate(self, value: Any) -> None:
        super().validate(value)
        if value and not self.URL_REGEX.match(str(value)):
            from fastframe.models.exceptions import ValidationError

            raise ValidationError(f"{self.verbose_name} must be a valid URL.")


class UUIDField(Field):
    """UUID v7 field (time-ordered, database-optimized).
    
    Always uses UUID v7 for better database performance:
    - Sequential inserts reduce index fragmentation
    - Natural chronological ordering
    - Better query performance
    - Can extract timestamp if needed
    
    Requires: uuid-utils package for Python < 3.14
    """

    def __init__(
        self, 
        *,
        generation: str | None = None,     # "python" or "database"
        **kwargs: Any
    ) -> None:
        """Initialize UUIDField with UUID v7 generation.
        
        Args:
            generation: "python" for Python-side generation (default),
                       "database" for database-side generation (requires DB support)
            **kwargs: Additional field options
        """
        from fastframe.conf import settings
        
        self.generation = generation or getattr(settings, 'UUID_GENERATION', 'python')
        
        if self.generation not in ("python", "database"):
            raise ValueError(
                f"UUID generation must be 'python' or 'database', got {self.generation}"
            )
        
        if "default" not in kwargs and self.generation == "python":
            # Python-side UUID v7 generation
            kwargs["default"] = self._get_uuid7_generator()
        
        elif self.generation == "database":
            # Database-side generation
            from sqlalchemy import text
            # Requires database extension/function (e.g., pg_uuidv7)
            kwargs["server_default"] = text("uuid_generate_v7()")
        
        super().__init__(**kwargs)
    
    @staticmethod
    def _get_uuid7_generator():
        """Get UUID v7 generator function."""
        # Try Python 3.14+ native uuid7
        if hasattr(uuid_module, 'uuid7'):
            return uuid_module.uuid7
        
        # Fall back to uuid-utils library
        try:
            from uuid_utils import uuid7
            return uuid7
        except ImportError:
            raise ImportError(
                "UUID v7 requires Python 3.14+ or the 'uuid-utils' package.\n"
                "Install with: pip install uuid-utils\n"
                "Or upgrade to Python 3.14+"
            )

    def get_sqlalchemy_type(self) -> Any:
        return UUID(as_uuid=True)

    def get_type_annotation(self) -> type:
        return Mapped[uuid_module.UUID]


class JSONField(Field):
    """JSON field (stored as TEXT in SQLite, JSON/JSONB in PostgreSQL/MySQL)."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize JSONField."""
        super().__init__(**kwargs)

    def get_sqlalchemy_type(self) -> Any:
        # SQLAlchemy's JSON type adapts to backend
        # (JSONB on Postgres, JSON on MySQL, TEXT on SQLite)
        from sqlalchemy import JSON

        return JSON

    def get_type_annotation(self) -> type:
        return Mapped[dict[str, Any]]


class ForeignKey(Field):
    """Foreign key field for model relationships.

    Example:
        author = fields.ForeignKey("User", on_delete="CASCADE", related_name="posts")
    """

    def __init__(
        self,
        to: str | type,
        *,
        on_delete: str = "RESTRICT",
        related_name: str | None = None,
        to_field: str = "id",
        **kwargs: Any,
    ) -> None:
        """Initialize ForeignKey.

        Args:
            to: Target model (string name or class).
            on_delete: What to do when referenced object is deleted:
                - "CASCADE": Delete this object too
                - "SET_NULL": Set FK to NULL (requires null=True)
                - "RESTRICT": Prevent deletion of referenced object
                - "SET_DEFAULT": Set FK to default value
            related_name: Name for reverse relationship on target model.
            to_field: Field on target model to reference (default "id").
            **kwargs: Additional field options.
        """
        if on_delete not in ("CASCADE", "SET_NULL", "RESTRICT", "SET_DEFAULT"):
            raise ValueError(
                f"on_delete must be CASCADE, SET_NULL, RESTRICT, or SET_DEFAULT, got {on_delete}"
            )

        if on_delete == "SET_NULL" and not kwargs.get("null", False):
            raise ValueError("on_delete='SET_NULL' requires null=True")

        self.to = to
        self.on_delete = on_delete
        self.related_name = related_name
        self.to_field = to_field
        self.relationship_name: str | None = None  # Set by ModelMeta

        # ForeignKey columns are nullable by default (unlike other fields)
        kwargs.setdefault("null", True)

        super().__init__(**kwargs)

    def get_sqlalchemy_type(self) -> Any:
        # Type is determined by the referenced field, but we need to return something
        # The actual type will be set by the ForeignKey constraint
        return Integer  # Most common case, will be overridden if needed

    def get_type_annotation(self) -> type:
        # Foreign keys store the ID, typically int
        return Mapped[int]

    def to_sqlalchemy_column(self) -> ColumnElement[Any]:
        """Convert ForeignKey to SQLAlchemy column.

        We create just the integer column here. The FK constraint and relationship
        will be set up by the ModelMeta metaclass after all models are defined.
        """
        # Just create the column without FK constraint for now
        # The constraint will be added in _setup_fk_relationships
        kwargs = {
            "nullable": self.null,
            **self.extra_kwargs,
        }

        if self.default is not NOT_PROVIDED:
            kwargs["default"] = self.default

        # Store FK info for later resolution
        return mapped_column(self.get_sqlalchemy_type(), **kwargs)


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
    "DecimalField",
    "EmailField",
    "URLField",
    "UUIDField",
    "JSONField",
    "ForeignKey",
]
