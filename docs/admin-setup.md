# Adding Admin to Your FastFrame Application

This guide shows you how to add the FastFrame admin interface to your application.

## Quick Start

### 1. Define Your Models

Create models in your app modules (Django-style structure recommended):

```python
# myapp/models.py
from fastframe.models import Model, fields


class Article(Model):
    title = fields.CharField(max_length=200)
    content = fields.TextField()
    published = fields.BooleanField(default=False)

    class Meta:
        db_table = "articles"
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        app_label = "myapp"
```

### 2. Configure Admin Classes

Create admin configuration in a separate file:

```python
# myapp/admin.py
from fastframe.admin import ModelAdmin, admin_site
from .models import Article


class ArticleAdmin(ModelAdmin):
    list_display = ["title", "published"]
    search_fields = ["title", "content"]
    list_filter = ["published"]
    list_per_page = 25


# Register your models
admin_site.register(Article, ArticleAdmin)
```

### 3. Include Admin in Your App

Choose one or more of the deployment options below.

## Deployment Options

FastFrame gives you three ways to deploy the admin:

### Option 1: REST API Only (Recommended)

Use the REST API with the React admin frontend (separate dev server or built):

```python
# app.py
from fastapi import FastAPI
from fastframe.admin import get_admin_api_router
from fastframe.core.bootstrap import bootstrap

bootstrap()

# Import your admin modules to register models
from myapp import admin  # noqa: E402, F401

app = FastAPI()

# Include the REST API at /api/admin/
app.include_router(get_admin_api_router())
```

**Development**: Run the React admin dev server separately:

```bash
cd admin-ui
npm install
npm run dev
```

Visit http://localhost:5173

**Production**: Build and serve the React admin from your FastAPI app:

```bash
cd admin-ui
npm run build
```

```python
# app.py (add this)
from fastapi.staticfiles import StaticFiles
from pathlib import Path

admin_ui_dist = Path(__file__).parent / "admin-ui" / "dist"
if admin_ui_dist.exists():
    app.mount("/admin", StaticFiles(directory=admin_ui_dist, html=True), name="admin")
```

Visit http://localhost:8000/admin

### Option 2: Server-Side Rendered Admin (Legacy)

Include the SSR admin at `/admin/`:

```python
from fastframe.admin import get_admin_router

app.include_router(get_admin_router())
```

Visit http://localhost:8000/admin/

**Note**: The SSR admin is legacy and only supports list/detail views. Use the REST API + React admin for create/edit/delete.

### Option 3: Both SSR and REST API

You can include both if you want:

```python
from fastframe.admin import get_admin_api_router, get_admin_router

# SSR admin at /admin/
app.include_router(get_admin_router())

# REST API at /api/admin/
app.include_router(get_admin_api_router())
```

### Option 4: No Admin

Simply don't include any admin routers. Your models and business logic work fine without the admin.

## Project Structure

Recommended Django-like structure:

```
myproject/
├── app.py                 # FastAPI app
├── config/
│   └── settings.py       # Database and settings
├── myapp/
│   ├── __init__.py
│   ├── models.py         # Models
│   └── admin.py          # Admin configuration
└── admin-ui/             # React admin (optional)
    ├── src/
    ├── package.json
    └── vite.config.ts
```

## Admin Customization

### ModelAdmin Options

```python
class ArticleAdmin(ModelAdmin):
    # List page
    list_display = ["title", "author", "published"]  # Columns to show
    search_fields = ["title", "content"]             # Fields to search
    list_filter = ["published", "author"]            # Filter sidebar
    list_per_page = 50                               # Pagination

    # Permissions
    has_add_permission = True
    has_change_permission = True
    has_delete_permission = True
    has_view_permission = True

    # Custom queryset
    def get_queryset(self, request):
        return super().get_queryset(request).filter(published=True)

    # Custom search
    def get_search_results(self, qs, search_term):
        return qs.filter(title__icontains=search_term)

    # Custom ordering
    def get_ordering(self):
        return ["-created_at", "title"]
```

### Field Options for Admin

```python
class Article(Model):
    # Exclude from admin responses (e.g., passwords)
    password = fields.CharField(max_length=255, write_only=True)

    # Read-only in forms
    created_at = fields.DateTimeField(auto_now_add=True)  # Auto read-only

    # Help text for forms
    title = fields.CharField(max_length=200, help_text="Article headline")

    # Choices appear as dropdowns
    status = fields.CharField(
        max_length=20,
        choices=[("draft", "Draft"), ("published", "Published")]
    )
```

## Example: Blog App

See `examples/blog_app/` for a complete working example with:
- Multiple apps (`users/`, `blog/`)
- Models with relationships
- Custom admin classes
- React admin UI
- All three deployment options demonstrated

## CORS for Development

If running the React admin dev server separately, add CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Next Steps

1. **React Admin UI**: Copy `examples/blog_app/admin-ui/` to your project and customize the theme
2. **Permissions**: Add authentication and role-based access control
3. **Actions**: Add bulk actions and custom endpoints
4. **Customization**: Override React admin components for your brand
