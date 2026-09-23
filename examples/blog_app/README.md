# Blog App - FastFrame Model Features Demo

This example project demonstrates all of FastFrame's Django-like ORM features in a realistic blog application context.

## Features Demonstrated

### ✅ Field Types
- **UUIDField**: Auto-generated UUID primary keys
- **CharField**: String fields with max_length
- **EmailField**: Email validation with regex
- **URLField**: URL validation  
- **TextField**: Long text content
- **IntegerField**: Integer numbers
- **BooleanField**: True/False with defaults
- **JSONField**: Structured JSON data
- **DateTimeField**: Timestamps with auto_now_add
- **DecimalField**: Precise decimal numbers

### ✅ Model Validation
- **Field-level validation**: Automatic validation for emails, URLs, max_length
- **Model-level validation**: Custom `clean()` method for business logic
- **full_clean()**: Orchestrates all validation
- **save(validate=True)**: Optional validation before save

### ✅ QuerySet & Lookups
- **Basic filters**: `filter(field=value)`
- **Field lookups**: `__gte`, `__lte`, `__gt`, `__lt`, `__in`, `__icontains`, `__iexact`, `__exact`, `__startswith`, `__endswith`, `__isnull`
- **Chaining**: `filter().filter().count()`
- **first()**: Get first result
- **all()**: Get all results

### ✅ Q Objects (Complex Queries)
- **OR queries**: `Q(karma__gte=50) | Q(username="alice")`
- **NOT queries**: `~Q(is_active=True)`
- **Complex combinations**: `(Q(a=1) & Q(b=2)) | Q(c=3)`

### ✅ F Objects (Field References)
- Reference model field values in queries
- Field-to-field comparisons
- Arithmetic operations

### ✅ ForeignKey Relationships
- **ForeignKey field**: Declarative foreign keys
- **Auto-generated relationships**: Access related objects automatically
- **on_delete options**: CASCADE, SET_NULL, RESTRICT, SET_DEFAULT
- **related_name**: Reverse relationships
- **Self-referential FKs**: Tree structures (categories, comments)

### ✅ Meta Options
- **db_table**: Custom table names
- **ordering**: Default ordering
- **unique_together**: Composite unique constraints
- **verbose_name**: Human-readable names

## Admin UI (React Admin)

The admin SPA lives in `admin-ui/` and talks to `GET/POST /api/admin/*`.

```bash
# API
python -m uvicorn app:app --host 127.0.0.1 --port 8000

# UI (another terminal)
cd admin-ui && npm install && npm run dev
```

Open http://localhost:5173

## Running the Demos

### Simple Demo (No ForeignKeys)
Tests all field types, validation, lookups, and Q objects:

```bash
python demo_simple.py
```

### Full Demo (With ForeignKeys) - Coming Soon
Demonstrates relationships, nested queries, and complex data modeling:

```bash
python demo.py  # Not yet fully working
```

## Project Structure

```
blog_app/
├── config/
│   └── settings.py          # FastFrame settings
├── users/                   # User models
│   ├── models.py
│   └── apps.py
├── posts/                   # Post & Category models  
│   ├── models.py
│   └── apps.py
├── comments/                # Comment models
│   ├── models.py
│   └── apps.py
├── manage.py               # Django-style management
├── demo_simple.py          # Simple feature demo
└── demo.py                 # Full feature demo (WIP)
```

## Next Steps

- ✅ Basic field types
- ✅ Model validation
- ✅ QuerySet lookups  
- ✅ Q/F objects
- ⏳ ForeignKey relationships (in progress)
- ⏳ Admin interface (coming soon)
- ⏳ Many-to-Many relationships
- ⏳ Signals
- ⏳ Custom managers

## Notes

This is a reference implementation showcasing FastFrame's ORM capabilities. It's intentionally comprehensive to serve as documentation and testing for the framework itself.
