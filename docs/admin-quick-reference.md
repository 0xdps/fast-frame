# FastFrame Admin Setup - Complete Guide

This document answers the three key questions about adding and deploying FastFrame admin.

## Question 1: How do I add admin to a new app?

### Quick Setup (5 minutes)

#### 1. Create Your Models

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

#### 2. Register with Admin

```python
# myapp/admin.py
from fastframe.admin import ModelAdmin, admin_site
from .models import Article

class ArticleAdmin(ModelAdmin):
    list_display = ["title", "published"]
    search_fields = ["title", "content"]
    list_filter = ["published"]

admin_site.register(Article, ArticleAdmin)
```

#### 3. Include in Your App

```python
# app.py
from fastapi import FastAPI
from fastframe.core.bootstrap import bootstrap

bootstrap()

# Import admin to register models
from myapp import admin  # noqa: E402

app = FastAPI()

# Add the REST API
from fastframe.admin import get_admin_api_router
app.include_router(get_admin_api_router())
```

That's it! Your models are now available at `/api/admin/`.

### React Admin UI (Optional)

To add the React admin frontend:

```bash
# Copy the admin-ui folder from examples/blog_app
cp -r examples/blog_app/admin-ui myproject/

# Install and run
cd admin-ui
npm install
npm run dev
```

Visit http://localhost:5173

**For production**, build and serve from your FastAPI server:

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

---

## Question 2: How do I deploy the admin?

You have **three flexible options** - choose what works for your project:

### Option 1: Same Server (Production Recommended) ⭐

Deploy the React admin from the same FastAPI server.

**Setup:**
```python
# app.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastframe.admin import get_admin_api_router

app = FastAPI()

# REST API at /api/admin/
app.include_router(get_admin_api_router())

# Built React admin at /admin
admin_ui_dist = Path(__file__).parent / "admin-ui" / "dist"
if admin_ui_dist.exists():
    app.mount("/admin", StaticFiles(directory=admin_ui_dist, html=True), name="admin")
```

**Deploy:**
```bash
cd admin-ui && npm run build
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Access:**
- Admin UI: http://yourserver.com/admin
- API: http://yourserver.com/api/admin/

**Pros:**
- ✅ Single server to manage
- ✅ No CORS issues
- ✅ Simple deployment
- ✅ Production-ready

**Cons:**
- ❌ Requires build step for UI changes

### Option 2: Separate Servers (Development Recommended) ⭐

Run API and React admin on different ports/domains.

**Setup:**
```python
# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastframe.admin import get_admin_api_router

app = FastAPI()

# CORS for separate React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://admin.yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# REST API only
app.include_router(get_admin_api_router())
```

**Deploy:**
```bash
# Terminal 1: API server
uvicorn app:app --host 0.0.0.0 --port 8000

# Terminal 2: React admin dev server
cd admin-ui && npm run dev  # Port 5173
```

**Access:**
- Admin UI: http://localhost:5173 (dev) or your CDN/static host (prod)
- API: http://localhost:8000/api/admin/

**Pros:**
- ✅ Hot reload during development
- ✅ Can deploy UI to CDN (Cloudflare Pages, Vercel, etc.)
- ✅ Faster UI iteration

**Cons:**
- ❌ CORS configuration needed
- ❌ Two servers to manage

### Option 3: No Admin

Don't include any admin routers - your models work fine without it.

```python
# app.py
from fastapi import FastAPI
from fastframe.core.bootstrap import bootstrap

bootstrap()

# Import models but not admin
from myapp import models  # noqa: E402

app = FastAPI()

# No admin routers - just your business logic
@app.get("/")
async def root():
    return {"message": "Hello World"}
```

**Use when:**
- Building an API without admin needs
- Using a different admin tool
- Admin will be added later

---

## Question 3: Project Structure Best Practices

### Recommended Structure

```
myproject/
├── app.py                     # FastAPI app setup
├── manage.py                  # CLI commands
├── config/
│   └── settings.py           # Database config
├── users/                     # Users app (like Django)
│   ├── __init__.py
│   ├── models.py             # User models
│   └── admin.py              # User admin
├── blog/                      # Blog app
│   ├── __init__.py
│   ├── models.py             # Blog models
│   └── admin.py              # Blog admin
└── admin-ui/                  # React admin (optional)
    ├── src/
    │   ├── App.tsx
    │   ├── dataProvider.ts
    │   ├── resources.tsx
    │   └── theme.ts
    └── package.json
```

### app.py Pattern

```python
#!/usr/bin/env python
"""
My FastFrame Application
"""
import os
import sys
from pathlib import Path

# Setup Python path and settings
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastapi import FastAPI
from fastframe.core.bootstrap import bootstrap
from fastframe.models import Model

# Bootstrap FastFrame
bootstrap()

# Import app modules (after bootstrap!)
from blog import admin as blog_admin  # noqa: E402, F401
from blog import models as blog_models  # noqa: E402, F401
from users import admin as users_admin  # noqa: E402, F401
from users import models as users_models  # noqa: E402, F401

# Create FastAPI app
app = FastAPI(title="My App")

# Choose your admin deployment option (see above)
from fastframe.admin import get_admin_api_router
app.include_router(get_admin_api_router())

# Create tables on startup
@app.on_event("startup")
async def startup():
    from fastframe.db.engine import get_engine
    engine = get_engine()
    Model.metadata.create_all(bind=engine)

# Your application routes
@app.get("/")
async def root():
    return {"message": "Welcome"}
```

### Module Pattern

**models.py:**
```python
from fastframe.models import Model, fields

class MyModel(Model):
    name = fields.CharField(max_length=100)
    
    class Meta:
        db_table = "mymodels"
        app_label = "myapp"  # Important!
```

**admin.py:**
```python
from fastframe.admin import ModelAdmin, admin_site
from .models import MyModel

class MyModelAdmin(ModelAdmin):
    list_display = ["name"]
    
admin_site.register(MyModel, MyModelAdmin)
```

---

## Complete Example

See `examples/blog_app/` for a fully working example demonstrating:
- ✅ Proper Django-like structure
- ✅ Multiple apps (users, blog)
- ✅ All three deployment options
- ✅ Custom admin configuration
- ✅ React admin with custom theme
- ✅ Password hashing and write-only fields
- ✅ Production-ready patterns

---

## Quick Reference

### Adding CORS for Development

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### ModelAdmin Options

```python
class MyAdmin(ModelAdmin):
    # List page
    list_display = ["field1", "field2"]
    search_fields = ["field1", "field3"]
    list_filter = ["field2"]
    list_per_page = 50
    
    # Permissions
    has_add_permission = True
    has_change_permission = True
    has_delete_permission = True
```

### Field Options for Admin

```python
# Hide from API responses (passwords, etc.)
password = fields.CharField(max_length=255, write_only=True)

# Read-only (auto timestamps)
created = fields.DateTimeField(auto_now_add=True)

# Help text in forms
title = fields.CharField(max_length=200, help_text="Article headline")

# Dropdown choices
status = fields.CharField(
    choices=[("draft", "Draft"), ("published", "Published")]
)
```

---

## Next Steps

1. ✅ Choose your deployment option
2. ✅ Structure your project (copy `examples/blog_app/` structure)
3. ✅ Create models with `Meta.app_label`
4. ✅ Register with `admin_site.register()`
5. ✅ Include admin router in FastAPI
6. ✅ Add authentication (coming soon in docs)
7. ✅ Customize React admin theme

**Need help?** Check:
- `examples/blog_app/` - Complete working example
- `docs/blog-app-restructuring.md` - Migration guide
- `examples/blog_app/README.md` - Usage guide
