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
            # Use DEFAULT_AUTO_FIELD setting to determine PK type
            try:
                from fastframe.conf import settings
                auto_field_type = settings.DEFAULT_AUTO_FIELD
            except (ImportError, AttributeError):
                # Fallback if settings not available
                auto_field_type = "AutoField"
            
            if auto_field_type == "AutoField":
                from fastframe.models.fields import AutoField
                auto_id = AutoField()
            elif auto_field_type == "BigAutoField":
                from fastframe.models.fields import BigAutoField
                auto_id = BigAutoField()
            elif auto_field_type == "UUIDField":
                from fastframe.models.fields import UUIDField
                auto_id = UUIDField(primary_key=True)
            else:
                raise ValueError(
                    f"Invalid DEFAULT_AUTO_FIELD: {auto_field_type}. "
                    f"Must be 'AutoField', 'BigAutoField', or 'UUIDField'."
                )
            
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

        # Store fields for later FK setup
        namespace["_fields_for_fk_setup"] = fields

        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        return cls


def _setup_fk_relationships(model_class: type, fields: dict[str, Any]) -> None:
    """Create FK constraints and relationship attributes for ForeignKey fields.

    For a field like `author_id = ForeignKey("Author")`, this creates:
    - FK constraint on author_id column (deferred until target table exists)
    - `author`: A relationship to the Author model
    - reverse: `posts` on Author (if related_name="posts")
    """
    from sqlalchemy import ForeignKey as SAForeignKey, event
    from sqlalchemy.orm import backref, relationship as sa_relationship

    from fastframe.models.fields import ForeignKey

    if not hasattr(model_class, "__table__"):
        return  # Table not yet created

    for field_name, field in fields.items():
        if not isinstance(field, ForeignKey):
            continue

        # Determine relationship attribute name
        # author_id → author, user_id → user
        if field_name.endswith("_id"):
            rel_attr_name = field_name[:-3]
        else:
            rel_attr_name = field_name + "_rel"

        # Get target model name
        if isinstance(field.to, str):
            target_model_name = field.to
        else:
            target_model_name = field.to.__name__

        # Add FK constraint to column
        # We need to resolve the target model to get its table name
        col = model_class.__table__.c.get(field_name)
        if col is not None:
            # Try to find target model in registry
            target_table_name = None
            if hasattr(model_class, "registry") and model_class.registry:
                for mapper in model_class.registry.mappers:
                    if mapper.class_.__name__ == target_model_name:
                        target_table_name = mapper.local_table.name
                        break
            
            if target_table_name:
                # Target found, add FK immediately
                fk_ref = f"{target_table_name}.{field.to_field}"
                fk = SAForeignKey(fk_ref, ondelete=field.on_delete)
                col.foreign_keys.add(fk)
                fk._set_parent(col)
            else:
                # Target not found yet, defer FK creation
                # Store FK info for later resolution
                def add_deferred_fk(mapper_registry, model_cls=model_class, col_obj=col, 
                                   target_name=target_model_name, fk_field=field):
                    """Add FK constraint after all mappers are configured."""
                    # Find target table
                    for m in mapper_registry.mappers:
                        if m.class_.__name__ == target_name:
                            tbl_name = m.local_table.name
                            fk_ref = f"{tbl_name}.{fk_field.to_field}"
                            if not col_obj.foreign_keys:  # Only add if not already present
                                fk = SAForeignKey(fk_ref, ondelete=fk_field.on_delete)
                                col_obj.foreign_keys.add(fk)
                                fk._set_parent(col_obj)
                            break
                
                # Register event to add FK after mapper configuration
                if hasattr(model_class, "registry"):
                    event.listen(
                        model_class.registry,
                        "after_configured",
                        add_deferred_fk,
                        once=True
                    )

        # Create the relationship
        rel_kwargs = {
            "lazy": "select",
        }

        if field.related_name:
            # Use backref to automatically create reverse relationship
            backref_kwargs = {
                "lazy": "select",
            }
            if field.on_delete == "CASCADE":
                backref_kwargs["cascade"] = "all, delete-orphan"
            
            rel_kwargs["backref"] = backref(field.related_name, **backref_kwargs)

        rel = sa_relationship(target_model_name, **rel_kwargs)

        # Set the relationship attribute on the model
        setattr(model_class, rel_attr_name, rel)

        # Store relationship name in field metadata for later use
        field.relationship_name = rel_attr_name


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

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a model instance, applying field defaults (Django-style).

        SQLAlchemy only applies ``default=`` at INSERT time, which leaves
        unset fields as None on new instances. Django instead applies defaults
        in ``__init__`` so instances are always in a valid in-memory state.
        We do the same: any field not passed gets its default applied here.
        """
        from fastframe.models.fields import NOT_PROVIDED

        fields_meta = self._meta.get("fields", {}) if hasattr(self, "_meta") else {}
        for field_name, field in fields_meta.items():
            if field_name in kwargs:
                continue
            default = getattr(field, "default", NOT_PROVIDED)
            if default is not NOT_PROVIDED:
                kwargs[field_name] = default() if callable(default) else default

        # Same behavior as SQLAlchemy's _declarative_constructor
        cls_attrs = type(self).__dict__
        for key, value in kwargs.items():
            if key not in cls_attrs and not hasattr(type(self), key):
                raise TypeError(
                    f"{type(self).__name__!r} is an invalid keyword argument "
                    f"for {type(self).__name__}"
                )
            setattr(self, key, value)

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

            raise ValidationError(errors=errors)

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
            
            # Setup FK relationships now that __table__ exists
            fields_for_fk = getattr(cls, "_fields_for_fk_setup", {})
            if fields_for_fk:
                _setup_fk_relationships(cls, fields_for_fk)
