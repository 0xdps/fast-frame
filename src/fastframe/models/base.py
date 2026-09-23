from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from sqlalchemy.orm import DeclarativeBase

from fastframe.models.manager import Manager

if TYPE_CHECKING:
    from fastframe.models.fields import Field


class ModelMeta(type(DeclarativeBase)):  # type: ignore[misc]
    """Metaclass that processes Field declarations into SQLAlchemy columns.

    When a Model subclass is created, this metaclass:
    1. Collects all Field instances from the class
    2. Processes Meta class options
    3. Converts fields to SQLAlchemy mapped_column()
    4. Auto-adds primary key if not specified
    5. Stores field metadata for admin introspection
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs: Any,
    ) -> type:
        # Don't process the base Model class itself
        if name == "Model" and not any(isinstance(b, ModelMeta) for b in bases):
            return super().__new__(mcs, name, bases, namespace, **kwargs)

        # Extract and process Meta class
        meta_class = namespace.pop("Meta", None)
        meta_options = {}
        if meta_class:
            for attr in dir(meta_class):
                if not attr.startswith("_"):
                    meta_options[attr] = getattr(meta_class, attr)

        # Collect Field instances from namespace
        fields: dict[str, Field] = {}
        for key, value in list(namespace.items()):
            # Import here to avoid circular dependency
            from fastframe.models.fields import Field

            if isinstance(value, Field):
                fields[key] = value
                value.model_class = name  # type: ignore[attr-defined]
                # Manually call __set_name__ since we're about to replace it
                value.__set_name__(None, key)  # type: ignore[arg-type]

        # Auto-add primary key if not present
        has_pk = any(f.primary_key for f in fields.values())
        if not has_pk and "id" not in fields:
            from fastframe.models.fields import AutoField

            auto_id = AutoField()
            auto_id.__set_name__(None, "id")  # type: ignore[arg-type]
            fields["id"] = auto_id

        # Convert fields to SQLAlchemy mapped_column and type annotations
        annotations = namespace.setdefault("__annotations__", {})
        for field_name, field in fields.items():
            # Add type annotation (e.g. Mapped[str])
            annotations[field_name] = field.get_type_annotation()
            # Replace Field instance with mapped_column()
            namespace[field_name] = field.to_sqlalchemy_column()

        # Apply Meta.db_table if specified
        if "db_table" in meta_options and "__tablename__" not in namespace:
            namespace["__tablename__"] = meta_options["db_table"]

        # Store metadata for introspection (admin forms, validation, etc.)
        namespace["_meta"] = {
            "fields": fields,
            "ordering": meta_options.get("ordering", []),
            "verbose_name": meta_options.get("verbose_name", name),
            "verbose_name_plural": meta_options.get(
                "verbose_name_plural", f"{name}s"
            ),
            "unique_together": meta_options.get("unique_together", []),
            "indexes": meta_options.get("indexes", []),
            **meta_options,
        }

        return super().__new__(mcs, name, bases, namespace, **kwargs)


class Model(DeclarativeBase, metaclass=ModelMeta):
    """SQLAlchemy declarative base with Django-like field API and manager.

    Example:
        from fastframe.models import Model, fields

        class Book(Model):
            title = fields.CharField(max_length=200)
            published = fields.DateField()

            class Meta:
                db_table = "books"
                ordering = ["-published"]
    """

    objects: ClassVar[Manager[Any]]

    def __repr__(self) -> str:
        """Return a Django-style repr showing primary key and attributes."""
        attrs = []
        for col in self.__table__.columns:
            val = getattr(self, col.name, None)
            if isinstance(val, str):
                val = repr(val)
            attrs.append(f"{col.name}={val}")
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"

    def clean(self) -> None:
        """Hook for custom model-level validation.

        Override this method to add validation logic that spans multiple fields.
        Raises ValidationError if validation fails.

        Example:
            def clean(self):
                if self.age < 18 and self.has_driver_license:
                    raise ValidationError("Underage drivers not allowed.")
        """

    def full_clean(self, exclude: list[str] | None = None) -> None:
        """Validate all fields and call clean().

        Args:
            exclude: List of field names to skip validation for.

        Raises:
            ValidationError: If any field or model validation fails.
        """
        exclude = exclude or []
        errors = {}

        # Validate each field
        for field_name, field in self._meta["fields"].items():
            if field_name in exclude:
                continue

            # Skip auto-incrementing primary keys (they're generated)
            from fastframe.models.fields import AutoField, BigAutoField

            if isinstance(field, (AutoField, BigAutoField)):
                continue

            try:
                value = getattr(self, field_name, None)
                field.validate(value)
            except Exception as e:
                errors[field_name] = str(e)

        # Call custom model-level validation
        try:
            self.clean()
        except Exception as e:
            errors["__all__"] = str(e)

        if errors:
            from fastframe.models.exceptions import ValidationError

            raise ValidationError(str(errors))

    def save(self, validate: bool = False) -> None:
        """Save the model instance to the database.

        Args:
            validate: If True, calls full_clean() before saving.
        """
        if validate:
            self.full_clean()

        from fastframe.db.session import get_current_session

        session = get_current_session()
        session.add(self)
        session.flush()

    def delete(self) -> None:
        from fastframe.db.session import get_current_session

        session = get_current_session()
        session.delete(self)
        session.flush()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not Model and getattr(cls, "__tablename__", None):
            cls.objects = Manager(cls)
