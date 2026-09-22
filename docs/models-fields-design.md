# Model Fields Design (v0.3)

**Status:** Design doc for implementation

FastFrame v0.3 introduces Django-style declarative field syntax to replace the current SQLAlchemy `mapped_column()` boilerplate.

## Current Problem

**Today's syntax (v0.1/v0.2):**
```python
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

class Todo(Model):
    __tablename__ = "todos"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

**Issues:**
- ❌ Verbose: must import `Mapped`, `mapped_column`, type classes
- ❌ Repetitive: `Mapped[str]` type hint + `String(200)` column type
- ❌ Not Django-like: users expect `CharField(max_length=200)`
- ❌ Admin can't introspect field metadata easily

## Proposed v0.3 Syntax

```python
from fastframe.models import Model, fields

class Todo(Model):
    class Meta:
        db_table = "todos"  # replaces __tablename__
    
    id = fields.AutoField(primary_key=True)  # Optional - auto-added if missing
    title = fields.CharField(max_length=200)
    done = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)
```

**Benefits:**
- ✅ Clean, declarative syntax
- ✅ Django-familiar for new users
- ✅ Admin can introspect `field.max_length`, `field.choices`, etc.
- ✅ Still compiles to SQLAlchemy underneath (migrations work)
- ✅ Escape hatch: can still use `mapped_column()` directly

---

## Field Types (v0.3 Scope)

### Core Fields

**AutoField / BigAutoField**
```python
id = fields.AutoField(primary_key=True)
# → mapped_column(Integer, primary_key=True, autoincrement=True)

big_id = fields.BigAutoField(primary_key=True)
# → mapped_column(BigInteger, primary_key=True, autoincrement=True)
```

**CharField**
```python
title = fields.CharField(max_length=200, blank=False, null=False, default="")
# → mapped_column(String(200), nullable=False, default="")
```
- `max_length`: required
- `blank`: validation hint (not enforced at DB, used by admin forms)
- `null`: translates to `nullable=` in SQLAlchemy
- `default`: Python-level default
- `db_default`: translates to `server_default=`

**TextField**
```python
content = fields.TextField(blank=True)
# → mapped_column(Text, nullable=False, default="")
```
- Like `CharField` but no `max_length`, uses `Text` type

**IntegerField / BigIntegerField**
```python
count = fields.IntegerField(default=0)
# → mapped_column(Integer, nullable=False, default=0)

huge_number = fields.BigIntegerField()
# → mapped_column(BigInteger)
```

**BooleanField**
```python
is_active = fields.BooleanField(default=True)
# → mapped_column(Boolean, nullable=False, default=True)
```
- Always `nullable=False` by default (booleans should be True/False, not NULL)

**DateTimeField / DateField / TimeField**
```python
created_at = fields.DateTimeField(auto_now_add=True)
# → mapped_column(DateTime, server_default=func.now())

updated_at = fields.DateTimeField(auto_now=True)
# → Requires Model.save() override to set on update

birth_date = fields.DateField()
# → mapped_column(Date)
```

**DecimalField**
```python
price = fields.DecimalField(max_digits=10, decimal_places=2)
# → mapped_column(Numeric(precision=10, scale=2))
```

**FloatField**
```python
rating = fields.FloatField()
# → mapped_column(Float)
```

### Relational Fields

**ForeignKey**
```python
author = fields.ForeignKey("User", on_delete="CASCADE", related_name="posts")
# → mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
# + relationship("User", back_populates="posts") auto-created
```
- `on_delete`: `"CASCADE"`, `"SET_NULL"`, `"RESTRICT"`, `"SET_DEFAULT"`
- `related_name`: reverse relationship name
- `to_field`: defaults to `"id"`

**ManyToManyField** (Deferred to v0.3.1+)
```python
tags = fields.ManyToManyField("Tag", through="PostTag")
# Complex - requires join table, needs more design
```

### Optional/Advanced Fields (v0.3.1+)

**EmailField** - CharField with validation
**URLField** - CharField with validation  
**UUIDField** - UUID primary keys
**JSONField** - Native JSON/JSONB
**FileField / ImageField** - Deferred until storage layer (v0.6+)

---

## Meta Class Options

```python
class Todo(Model):
    title = fields.CharField(max_length=200)
    
    class Meta:
        db_table = "todos"              # replaces __tablename__
        ordering = ["-created_at"]       # default QuerySet ordering
        unique_together = [["user", "slug"]]  # composite unique
        indexes = [
            {"fields": ["created_at"], "name": "idx_created"},
        ]
        verbose_name = "Todo Item"
        verbose_name_plural = "Todo Items"
```

**Meta options:**
- `db_table` (required if no `__tablename__`) - table name
- `ordering` - default order for `Model.objects.all()`
- `unique_together` - composite unique constraints
- `indexes` - additional indexes
- `verbose_name` / `verbose_name_plural` - admin display names
- `abstract = True` - for abstract base models

---

## Implementation Architecture

### Field Base Class

```python
# fastframe/models/fields.py

class Field:
    """Base class for all model fields."""
    
    def __init__(
        self,
        *,
        primary_key=False,
        unique=False,
        null=False,
        blank=False,
        default=NOT_PROVIDED,
        db_default=None,
        choices=None,
        help_text="",
        verbose_name=None,
        validators=None,
        **kwargs,
    ):
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
        
        self.name = None  # Set by __set_name__
        self.model = None  # Set by ModelMeta
    
    def __set_name__(self, owner, name):
        """Called when field is assigned to a class."""
        self.name = name
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()
    
    def to_sqlalchemy_column(self):
        """Convert to SQLAlchemy mapped_column()."""
        raise NotImplementedError
    
    def get_type_annotation(self):
        """Return Mapped[...] type for this field."""
        raise NotImplementedError
```

### ModelMeta Metaclass

```python
# fastframe/models/base.py

class ModelMeta(type):
    """Metaclass that processes Field declarations."""
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Extract Meta class
        meta = namespace.pop("Meta", None)
        
        # Collect fields
        fields = {}
        for key, value in list(namespace.items()):
            if isinstance(value, Field):
                fields[key] = value
                value.model = name
        
        # Auto-add primary key if not present
        if not any(f.primary_key for f in fields.values()):
            if "id" not in fields:
                fields["id"] = AutoField(primary_key=True)
        
        # Convert fields to SQLAlchemy mapped_column
        for field_name, field in fields.items():
            # Set type annotation
            namespace["__annotations__"][field_name] = field.get_type_annotation()
            # Set mapped_column
            namespace[field_name] = field.to_sqlalchemy_column()
        
        # Process Meta options
        if meta:
            if hasattr(meta, "db_table"):
                namespace["__tablename__"] = meta.db_table
            if hasattr(meta, "ordering"):
                namespace["_meta_ordering"] = meta.ordering
        
        # Store field metadata for admin introspection
        namespace["_meta_fields"] = fields
        
        return super().__new__(mcs, name, bases, namespace, **kwargs)
```

### Concrete Field Implementation Example

```python
# fastframe/models/fields.py

class CharField(Field):
    def __init__(self, max_length, **kwargs):
        if max_length is None:
            raise ValueError("CharField requires max_length")
        self.max_length = max_length
        super().__init__(**kwargs)
    
    def to_sqlalchemy_column(self):
        from sqlalchemy import String
        from sqlalchemy.orm import mapped_column
        
        return mapped_column(
            String(self.max_length),
            primary_key=self.primary_key,
            unique=self.unique,
            nullable=self.null,
            default=self.default if self.default is not NOT_PROVIDED else None,
            server_default=self.db_default,
        )
    
    def get_type_annotation(self):
        from sqlalchemy.orm import Mapped
        return Mapped[str]
```

---

## Migration Compatibility

**Key requirement:** Fields must compile to standard SQLAlchemy columns so Alembic autogenerate works unchanged.

**Verification:**
```python
# After implementing fields:
class Book(Model):
    title = fields.CharField(max_length=200)

# Should be equivalent to:
class Book(Model):
    title: Mapped[str] = mapped_column(String(200))

# Alembic sees the same metadata in both cases
```

---

## Validation & Forms

Fields store validation metadata for admin forms:

```python
class CharField(Field):
    def validate(self, value):
        """Called by Model.full_clean() or admin forms."""
        if not self.blank and not value:
            raise ValidationError(f"{self.verbose_name} cannot be blank")
        if len(value) > self.max_length:
            raise ValidationError(f"Max length is {self.max_length}")
        for validator in self.validators:
            validator(value)
```

---

## Backward Compatibility

**Old syntax still works:**
```python
# v0.1/v0.2 style - still valid in v0.3+
class User(Model):
    email: Mapped[str] = mapped_column(String(255), unique=True)
```

**New syntax preferred:**
```python
# v0.3+ style - recommended
class User(Model):
    email = fields.CharField(max_length=255, unique=True)
```

**Both can be mixed** (for gradual migration):
```python
class User(Model):
    # Old style
    id: Mapped[int] = mapped_column(primary_key=True)
    
    # New style
    email = fields.CharField(max_length=255)
```

---

## Admin Integration

Admin introspects field metadata:

```python
@admin.register(Book)
class BookAdmin(ModelAdmin):
    # Admin auto-generates form from Book._meta_fields:
    # - CharField → <input type="text" maxlength="200">
    # - BooleanField → <input type="checkbox">
    # - ForeignKey → <select> or autocomplete
    # - DateTimeField → datetime picker
    pass
```

---

## Testing Strategy

1. **Field to SQLAlchemy mapping** - verify each field type produces correct `mapped_column()`
2. **Migrations** - ensure Alembic detects changes correctly
3. **Admin introspection** - verify `_meta_fields` contains expected metadata
4. **Backward compat** - old `mapped_column()` syntax still works
5. **Validation** - `field.validate()` catches invalid data

---

## Next Steps

1. Implement base `Field` class + `ModelMeta` metaclass
2. Implement core field types (Char, Text, Integer, Boolean, DateTime, Decimal)
3. Test migration generation (should be identical to `mapped_column()`)
4. Update project templates to use new syntax
5. Document escape hatch (when to use `mapped_column()` directly)
6. Implement `ForeignKey` (more complex due to relationships)
7. Admin forms use field metadata (v0.3 later)
