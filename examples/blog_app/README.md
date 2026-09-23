# Blog App - FastFrame Admin Demo

This example demonstrates FastFrame's admin interface with a properly structured Django-like application.

## Project Structure

```
blog_app/
├── app.py                 # FastAPI application
├── config/
│   └── settings.py       # Database and settings
├── users/                 # Users app
│   ├── __init__.py
│   ├── models.py         # SimpleUser model
│   └── admin.py          # User admin configuration
├── blog/                  # Blog app
│   ├── __init__.py
│   ├── models.py         # Category, Post, Tag, Comment
│   └── admin.py          # Blog admin configuration
├── admin-ui/              # React admin frontend
│   ├── src/
│   │   ├── App.tsx       # Main app with resource setup
│   │   ├── dataProvider.ts
│   │   ├── resources.tsx
│   │   ├── users.tsx     # Custom user views
│   │   └── theme.ts
│   └── package.json
├── populate_db.py         # Sample data seeder
└── manage.py              # CLI commands
```

## Features Demonstrated

### ✅ Project Organization
- **Django-like apps**: `users/` and `blog/` with separate models and admin
- **Clean imports**: Models and admin classes in dedicated modules
- **Reusable**: Copy this structure for your own projects

### ✅ Admin Deployment Options

**Option 1: REST API + React Admin (Current)**
- API at `/api/admin/`
- React dev server at http://localhost:5173 (development)
- Or build and serve from `/admin` (production)

**Option 2: SSR Admin (Legacy, optional)**
- Uncomment `get_admin_router()` in `app.py`
- Server-rendered at `/admin/`

**Option 3: No Admin**
- Comment out all admin routers
- Models work fine without admin

### ✅ Models

**Users App:**
- `SimpleUser` - Account with password hashing, preferences (JSON)

**Blog App:**
- `Category` - Blog categories
- `Post` - Blog posts with status, views, likes
- `Tag` - Content tags
- `Comment` - Post comments with approval

### ✅ Admin Features
- Custom list views with search and filters
- Create, edit, delete operations
- Password change action for users
- Full-width user profile with header
- Custom theme (dark sidebar, Outfit + Figtree fonts)
- Responsive tables and forms

## Quick Start

### 1. Create and Populate Database

```bash
rm -f blog.db
python populate_db.py
```

Creates 3 users, 3 categories, 5 posts, 5 tags, and 4 comments.

### 2. Start the API Server

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

API available at http://127.0.0.1:8000
- REST API: http://127.0.0.1:8000/api/admin/
- Docs: http://127.0.0.1:8000/docs

### 3. Start the React Admin (Development)

In a separate terminal:

```bash
cd admin-ui
npm install
npm run dev
```

Admin UI at http://localhost:5173

## Admin Customization

See `../../docs/admin-setup.md` for:
- How to add admin to your own app
- Deployment options (same server vs separate)
- ModelAdmin configuration
- Custom views and permissions

## Model Examples

The demo includes examples of all FastFrame ORM features:

### Field Types
- UUID primary keys (`SimpleUser.id`)
- Email validation (`SimpleUser.email`)
- JSON fields (`SimpleUser.preferences`)
- Text fields (`Post.content`)
- Choices (`Post.status`)
- Boolean flags (`Post.is_featured`)
- Integers (`Post.view_count`)
- Write-only fields (`SimpleUser.password`)

### Validation
```python
class SimpleUser(Model):
    def clean(self):
        if not self.username.replace("_", "").isalnum():
            raise ValidationError("Username must be alphanumeric")
```

### Password Hashing
```python
@validates("password")
def _hash_password(self, _key: str, value: str | None) -> str | None:
    if not value:
        return value
    return hash_password(value)
```

### Meta Options
```python
class Post(Model):
    class Meta:
        db_table = "posts"
        ordering = ["-id"]
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        app_label = "blog"
```

### Admin Configuration
```python
class PostAdmin(ModelAdmin):
    list_display = ["title", "status", "is_featured", "view_count", "like_count"]
    search_fields = ["title", "content", "summary"]
    list_filter = ["status", "is_featured"]
    list_per_page = 25
```

## Production Deployment

### Build the React Admin

```bash
cd admin-ui
npm run build
```

### Serve from FastAPI

Uncomment in `app.py`:

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path

admin_ui_dist = Path(__file__).parent / "admin-ui" / "dist"
if admin_ui_dist.exists():
    app.mount("/admin", StaticFiles(directory=admin_ui_dist, html=True), name="admin")
```

Now the admin is at http://127.0.0.1:8000/admin (same server as the API).

## Other Demo Scripts

### demo_simple.py
Simple demonstrations without foreign keys:
```bash
python demo_simple.py
```

Tests field types, validation, lookups, Q objects, and F expressions.

### demo.py
Full demonstrations (work in progress):
```bash
python demo.py
```

Tests foreign keys, relationships, and complex queries.

## CLI Commands

```bash
# Create database tables
python manage.py migrate

# Show migrations
python manage.py showmigrations

# Database shell
python manage.py dbshell

# Run tests
python manage.py test
```

## Troubleshooting

**Q: Port 8000 already in use?**
```bash
lsof -ti:8000 | xargs kill -9
```

**Q: Port 5173 already in use?**
```bash
lsof -ti:5173 | xargs kill -9
```

**Q: React admin can't connect to API?**
- Check CORS in `app.py` includes your dev server origin
- Verify API is running on port 8000
- Check browser console for errors

**Q: Schema changes not appearing?**
- Restart the API server
- Clear browser cache
- Check models are imported in `app.py`

## Next Steps

1. **Copy this structure** to your own FastFrame app
2. **Customize the models** in `users/` and `blog/`
3. **Customize the admin** configuration and theme
4. **Add authentication** to protect admin routes
5. **Add relationships** between your models
6. **Deploy to production** with the built React admin

See `../../docs/admin-setup.md` for the complete guide.
