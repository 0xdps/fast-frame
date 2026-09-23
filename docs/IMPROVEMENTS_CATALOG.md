# FastFrame Improvements Catalog
**Version:** 0.2.0  
**Date:** September 23, 2026

---

## 1. Performance Improvements

### 1.1 Database & ORM

#### **QuerySet Result Caching**
**Current Behavior:**
```python
books = Book.objects.filter(published=True)
for book in books:  # Query executed
    print(book.title)

for book in books:  # Query executed AGAIN ❌
    print(book.author)
```

**Desired Behavior:**
```python
books = Book.objects.filter(published=True)
for book in books:  # Query executed
    print(book.title)

for book in books:  # Uses cached results ✅
    print(book.author)
```

**Implementation:**
- Add `_result_cache` to QuerySet
- Cache results after first iteration
- Invalidate on filter/exclude/order_by
- **Effort:** Small (1 day)
- **Impact:** Medium (reduces duplicate queries)

---

#### **Lazy Model Loading**
**Current Behavior:**
- All models imported on bootstrap
- CLI commands are slow even for simple tasks

**Desired Behavior:**
- Import models only when needed
- `manage.py --help` should be instant

**Implementation:**
- Defer model imports until first use
- Use `importlib` for lazy loading
- **Effort:** Medium (2-3 days)
- **Impact:** High (faster CLI)

---

#### **Connection Pooling**
**Current Behavior:**
- Single connection per request
- No connection reuse

**Desired Behavior:**
- Connection pool (e.g., 5-20 connections)
- Reuse connections across requests

**Implementation:**
- SQLAlchemy `pool_size` and `max_overflow`
- Add to settings: `DATABASE_POOL_SIZE = 10`
- **Effort:** Small (1 day)
- **Impact:** High (better concurrency)

---

#### **select_related / prefetch_related**
**Current Behavior:**
```python
# N+1 queries ❌
books = Book.objects.all()
for book in books:
    print(book.author.name)  # Query per book
```

**Desired Behavior:**
```python
# 2 queries total ✅
books = Book.objects.select_related("author").all()
for book in books:
    print(book.author.name)  # No additional queries
```

**Implementation:**
- Add `select_related()` for ForeignKey (SQL JOIN)
- Add `prefetch_related()` for reverse FK / M2M (separate query + Python join)
- **Effort:** Large (1 week)
- **Impact:** High (eliminates N+1 queries)

---

### 1.2 Admin Performance

#### **Admin List View Pagination**
**Current Behavior:**
- Loads all model instances
- No default limit

**Desired Behavior:**
- Default pagination (100 items/page)
- Configurable via `ModelAdmin.list_per_page`

**Implementation:**
- Add pagination to list API endpoint
- Update React UI to handle pages
- **Effort:** Small (1 day)
- **Impact:** High (prevents OOM on large tables)

---

#### **Admin ForeignKey Autocomplete**
**Current Behavior:**
- Dropdown loads all related objects
- Slow with 1000+ options

**Desired Behavior:**
- Autocomplete with search
- Loads only first 50, searches on type

**Implementation:**
- Add autocomplete API endpoint
- Update React UI with Select component
- **Effort:** Medium (2-3 days)
- **Impact:** High (usable with large datasets)

---

## 2. Developer Experience Improvements

### 2.1 Error Messages

#### **Better Model Validation Errors**
**Current Behavior:**
```python
ValidationError: {'name': 'This field is required.'}
```

**Desired Behavior:**
```python
ValidationError: Book validation failed:
  - name: This field is required.
  - price: Must be a positive number.
```

**Implementation:**
- Improve `ValidationError.__str__()`
- Add field names and model name to error
- **Effort:** Trivial (1 hour)
- **Impact:** Medium (better debugging)

---

#### **SQL Query Logging in Dev**
**Current Behavior:**
- No visibility into SQL queries
- Hard to debug performance issues

**Desired Behavior:**
```python
# In dev mode with DEBUG=True:
[DEBUG] SQL: SELECT * FROM books WHERE published = True (0.002s)
[DEBUG] SQL: SELECT * FROM users WHERE id = 5 (0.001s)
```

**Implementation:**
- Add SQLAlchemy `echo=True` when `DEBUG=True`
- Pretty-print queries with timing
- **Effort:** Small (1 day)
- **Impact:** High (easier debugging)

---

#### **Migration Conflict Detection**
**Current Behavior:**
- Parallel branches create conflicting migrations
- Conflicts discovered only on merge

**Desired Behavior:**
```bash
$ manage.py makemigrations
Error: Migration conflict detected:
  - 0003_auto_20260920_1234.py
  - 0003_auto_20260920_5678.py
Run `manage.py migrate --merge` to resolve.
```

**Implementation:**
- Detect multiple heads in Alembic
- Add `migrate --merge` command
- **Effort:** Medium (2-3 days)
- **Impact:** Medium (prevents merge conflicts)

---

### 2.2 CLI Enhancements

#### **Interactive Model Creation**
**Current Behavior:**
```bash
$ manage.py shell
>>> user = User(username="alice", email="alice@example.com")
>>> user.save()
```

**Desired Behavior:**
```bash
$ manage.py create user
Username: alice
Email: alice@example.com
First name: Alice
Last name: Smith
Created: User(id=1, username="alice")
```

**Implementation:**
- Add `manage.py create <model>` command
- Interactive prompts for fields
- **Effort:** Medium (2-3 days)
- **Impact:** Low (nice to have)

---

#### **Data Seeding Command**
**Current Behavior:**
- Manual `populate_db.py` scripts
- No standard approach

**Desired Behavior:**
```bash
$ manage.py seed
Seeding database with test data...
  Created 10 users
  Created 50 blog posts
  Created 200 comments
Done!
```

**Implementation:**
- Add `manage.py seed` command
- Look for `<app>/seeds.py` or `<app>/fixtures.json`
- **Effort:** Medium (2-3 days)
- **Impact:** Medium (easier testing/demo)

---

### 2.3 Testing Improvements

#### **Test Database Auto-Creation**
**Current Behavior:**
```python
# tests/conftest.py
@pytest.fixture(scope="session")
def project_env():
    os.environ["DATABASE_URL"] = "sqlite:///./test_db.sqlite3"
    # Manual cleanup
```

**Desired Behavior:**
```python
# Automatic test database
$ manage.py test
Creating test database: test_db.sqlite3
Running tests...
Destroying test database
```

**Implementation:**
- Detect test mode
- Auto-create temp database
- Auto-destroy after tests
- **Effort:** Medium (2-3 days)
- **Impact:** High (better isolation)

---

#### **Test Fixtures (like Django)**
**Current Behavior:**
- Manual data creation in each test
- Lots of boilerplate

**Desired Behavior:**
```python
@pytest.fixture
def sample_books():
    return [
        Book.objects.create(title="Book 1"),
        Book.objects.create(title="Book 2"),
    ]

def test_book_list(sample_books):
    assert Book.objects.count() == 2
```

**Implementation:**
- Create reusable fixture library
- Document patterns
- **Effort:** Small (1 day)
- **Impact:** Medium (less boilerplate)

---

## 3. Feature Completeness

### 3.1 Model Features

#### **Model Inheritance**
**Current Behavior:**
- Not supported
- Manual duplication

**Desired Behavior:**
```python
class BaseModel(Model):
    created_at = fields.DateTimeField(auto_now_add=True)
    updated_at = fields.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

class Post(BaseModel):
    title = fields.CharField(max_length=200)
    # Inherits created_at, updated_at ✅
```

**Implementation:**
- Support `class Meta: abstract = True`
- SQLAlchemy declarative inheritance
- **Effort:** Medium (3-4 days)
- **Impact:** High (reduces duplication)

---

#### **Soft Delete**
**Current Behavior:**
```python
book.delete()  # Hard delete from DB
```

**Desired Behavior:**
```python
book.delete()  # Sets deleted_at = now()
Book.objects.all()  # Excludes deleted
Book.objects.with_deleted()  # Includes deleted
```

**Implementation:**
- Add `deleted_at` field
- Override `delete()` to soft delete
- Add `with_deleted()` manager method
- **Effort:** Medium (2-3 days)
- **Impact:** Medium (data recovery)

---

#### **Model Signals (Events)**
**Current Behavior:**
- No hooks for model lifecycle
- Manual coordination

**Desired Behavior:**
```python
from fastframe.models import signals

@signals.pre_save.connect(sender=Book)
def on_book_save(sender, instance):
    print(f"About to save: {instance}")

@signals.post_delete.connect(sender=Book)
def on_book_delete(sender, instance):
    print(f"Deleted: {instance}")
```

**Implementation:**
- Add signal dispatcher
- Emit signals from `save()`, `delete()`
- **Effort:** Medium (3-4 days)
- **Impact:** Medium (enables plugins)

---

### 3.2 Admin Features

#### **Admin Filters**
**Current Behavior:**
- No filtering in admin list view

**Desired Behavior:**
```python
class BookAdmin(ModelAdmin):
    list_filter = ["published", "category", "author"]
```

**Implementation:**
- Add filter sidebar in React UI
- Query API with filter params
- **Effort:** Medium (2-3 days)
- **Impact:** High (essential for usability)

---

#### **Admin Actions**
**Current Behavior:**
- No bulk actions

**Desired Behavior:**
```python
class BookAdmin(ModelAdmin):
    actions = ["publish_books", "delete_books"]
    
    def publish_books(self, request, queryset):
        queryset.update(published=True)
```

**Implementation:**
- Add action dropdown in React UI
- POST to `/admin/bulk-action` endpoint
- **Effort:** Medium (3-4 days)
- **Impact:** Medium (productivity)

---

#### **Admin Inline Editing**
**Current Behavior:**
- Edit form is separate view
- Slow workflow

**Desired Behavior:**
- Inline editing in list view
- Click to edit, auto-save on blur

**Implementation:**
- Editable cells in React table
- PATCH to update endpoint
- **Effort:** Large (1 week)
- **Impact:** High (faster editing)

---

### 3.3 Authentication Features

#### **Login/Logout Views**
**Current Behavior:**
- No authentication system

**Desired Behavior:**
```python
# Auto-included routes:
# POST /auth/login
# POST /auth/logout
# POST /auth/refresh (JWT)
```

**Implementation:**
- Session-based auth
- JWT token auth (optional)
- Cookie management
- **Effort:** Large (1 week)
- **Impact:** High (enables secured apps)

---

#### **Password Reset Flow**
**Current Behavior:**
- Manual implementation required

**Desired Behavior:**
```python
# POST /auth/password-reset
# POST /auth/password-reset/confirm
```

**Implementation:**
- Token generation
- Email integration
- Reset form
- **Effort:** Medium (3-4 days)
- **Impact:** Medium (common use case)

---

#### **OAuth Integration**
**Current Behavior:**
- Not supported

**Desired Behavior:**
```python
# settings.py
OAUTH_PROVIDERS = {
    "google": {"client_id": "...", "client_secret": "..."},
    "github": {"client_id": "...", "client_secret": "..."},
}
```

**Implementation:**
- OAuth2 flow (authlib or httpx-oauth)
- Provider callbacks
- **Effort:** Large (1-2 weeks)
- **Impact:** High (modern auth)

---

## 4. Code Quality & Maintainability

### 4.1 Type Safety

#### **Stricter Type Hints**
**Current Behavior:**
- Some `Any` types
- No mypy enforcement

**Desired Behavior:**
- Full type coverage
- mypy `--strict` passes

**Implementation:**
- Add type stubs for SQLAlchemy
- Fix `Any` types
- Enable mypy in CI
- **Effort:** Large (1 week)
- **Impact:** Medium (catches bugs early)

---

#### **Generic QuerySet Typing**
**Current Behavior:**
```python
books = Book.objects.all()  # QuerySet (no type info)
```

**Desired Behavior:**
```python
books = Book.objects.all()  # QuerySet[Book] ✅
reveal_type(books[0])  # Book ✅
```

**Implementation:**
- Better Generic[T] usage
- Manager type stubs
- **Effort:** Medium (2-3 days)
- **Impact:** Medium (better IDE autocomplete)

---

### 4.2 Testing

#### **Property-Based Testing**
**Current Behavior:**
- Manual test cases
- Edge cases missed

**Desired Behavior:**
```python
from hypothesis import given, strategies as st

@given(st.text(max_size=200))
def test_book_title_validation(title):
    book = Book(title=title)
    book.full_clean()  # Should never crash
```

**Implementation:**
- Add `hypothesis` dependency
- Write property tests for validators
- **Effort:** Medium (3-4 days)
- **Impact:** High (finds edge case bugs)

---

#### **Mutation Testing**
**Current Behavior:**
- Tests may pass even if code is broken
- No way to verify test quality

**Desired Behavior:**
```bash
$ manage.py mutate
Running mutation tests...
Killed: 85/100 mutants
Survived: 15/100 (need more tests)
```

**Implementation:**
- Integrate `mutmut` or `cosmic-ray`
- **Effort:** Small (1 day)
- **Impact:** Medium (improves test quality)

---

### 4.3 Documentation

#### **API Reference (Auto-Generated)**
**Current Behavior:**
- Manual documentation
- Often out of sync

**Desired Behavior:**
```bash
$ manage.py docs
Generating API docs from docstrings...
Docs written to docs/api/
```

**Implementation:**
- Sphinx or MkDocs
- Auto-extract docstrings
- **Effort:** Medium (2-3 days)
- **Impact:** High (always up-to-date docs)

---

#### **Interactive Examples (Jupyter)**
**Current Behavior:**
- Static examples only

**Desired Behavior:**
- Jupyter notebooks in `examples/notebooks/`
- Interactive model exploration

**Implementation:**
- Add notebook examples
- Document setup
- **Effort:** Small (1 day)
- **Impact:** Medium (better learning)

---

## 5. Production Readiness

### 5.1 Observability

#### **Structured Logging**
**Current Behavior:**
- Print statements
- No log levels

**Desired Behavior:**
```python
import logging
logger = logging.getLogger(__name__)

logger.info("User created", extra={"user_id": user.id})
logger.warning("Slow query", extra={"duration": 2.5})
```

**Implementation:**
- Configure Python logging
- JSON log formatter
- **Effort:** Small (1 day)
- **Impact:** High (debugging in production)

---

#### **Metrics & Tracing**
**Current Behavior:**
- No metrics collection

**Desired Behavior:**
- Prometheus metrics endpoint
- OpenTelemetry tracing
- Request duration, DB query count

**Implementation:**
- Add `prometheus-fastapi-instrumentator`
- Add `opentelemetry-instrumentation-fastapi`
- **Effort:** Medium (2-3 days)
- **Impact:** High (production monitoring)

---

### 5.2 Deployment

#### **Health Check Endpoint**
**Current Behavior:**
- Manual implementation

**Desired Behavior:**
```python
# GET /health
# Checks:
# - Database connectivity
# - Migrations up to date
# - Dependencies available
```

**Implementation:**
- Add `health` endpoint
- Run check framework
- **Effort:** Small (1 day)
- **Impact:** High (k8s readiness probe)

---

#### **Docker Support**
**Current Behavior:**
- No official Docker image

**Desired Behavior:**
```dockerfile
FROM python:3.12
RUN pip install fastframe
# ...auto-configured...
```

**Implementation:**
- Create Dockerfile template
- Docker Compose for dev
- **Effort:** Small (1 day)
- **Impact:** Medium (easier deployment)

---

#### **Cloud Platform Integrations**
**Current Behavior:**
- Manual setup required

**Desired Behavior:**
```bash
$ fastframe deploy heroku
$ fastframe deploy railway
$ fastframe deploy fly
```

**Implementation:**
- CLI deploy commands
- Platform-specific configs
- **Effort:** Large (2 weeks)
- **Impact:** High (easier adoption)

---

## 6. Security Improvements

### 6.1 Input Validation

#### **SQL Injection Protection Audit**
**Current Behavior:**
- Using SQLAlchemy (should be safe)
- Not audited

**Tasks:**
- [ ] Audit QuerySet lookups for SQL injection
- [ ] Test with malicious inputs
- [ ] Document safe usage patterns

**Effort:** Medium (2-3 days)  
**Impact:** Critical (security)

---

#### **CSRF Protection**
**Current Behavior:**
- Not implemented

**Desired Behavior:**
- CSRF token in forms
- Validated on POST/PUT/DELETE

**Implementation:**
- Add CSRF middleware
- Token generation/validation
- **Effort:** Medium (2-3 days)
- **Impact:** High (prevents attacks)

---

### 6.2 Secrets Management

#### **Secrets in Settings**
**Current Behavior:**
```python
SECRET_KEY = "dev-secret-key-change-in-production"  # ⚠️ Risky
```

**Desired Behavior:**
```python
SECRET_KEY = os.getenv("SECRET_KEY")  # ✅ From env
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY not set")
```

**Implementation:**
- Validate required settings on bootstrap
- Error on missing secrets in production
- **Effort:** Small (1 day)
- **Impact:** High (prevents deployment issues)

---

### 6.3 Rate Limiting

#### **Admin API Rate Limiting**
**Current Behavior:**
- No rate limiting
- Vulnerable to brute force

**Desired Behavior:**
```python
# 100 requests per minute per IP
@rate_limit(limit=100, window=60)
async def admin_api():
    ...
```

**Implementation:**
- Add `slowapi` or custom middleware
- Redis backend for distributed limits
- **Effort:** Medium (2-3 days)
- **Impact:** High (prevents abuse)

---

## Priority Matrix

### High Impact, Low Effort (Do First) 🎯
1. QuerySet result caching
2. SQL query logging
3. Better error messages
4. Health check endpoint
5. Structured logging

### High Impact, High Effort (Strategic) 🚀
1. select_related / prefetch_related
2. Authentication system
3. Admin filters & actions
4. Connection pooling
5. Type safety (mypy)

### Low Impact, Low Effort (Quick Wins) ✨
1. Data seeding command
2. Docker support
3. Interactive examples
4. Better admin pagination

### Low Impact, High Effort (Defer) ⏸️
1. OAuth integration (until v0.5+)
2. Cloud deploy commands (until v0.6+)
3. Jupyter notebooks (nice to have)
4. Inline admin editing (v0.4+)

---

*Improvements catalog updated: 2026-09-23*  
*Contributions welcome: See CONTRIBUTING.md*
