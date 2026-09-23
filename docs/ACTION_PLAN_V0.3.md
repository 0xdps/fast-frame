# FastFrame v0.3 Action Plan
**Based on**: Audit 2026-09-23  
**Target**: Complete v0.3 release

---

## Critical Path to v0.3.0 Release

### Phase 1: Core Blockers (1 week) — **MUST COMPLETE**

#### 1.1 Relationship Auto-Generation ⚠️ **BLOCKER**
**Priority:** P0  
**Effort:** 2-3 days  
**Owner:** TBD

**Problem:**
```python
class Book(Model):
    author = fields.ForeignKey("User", on_delete="CASCADE", related_name="books")

# Currently: Manual relationship() required ❌
# Expected: Auto-generated relationship() ✅
# Book.author → User instance
# User.books → QuerySet[Book]
```

**Tasks:**
- [ ] Update `ModelMeta` to detect `ForeignKey` fields
- [ ] Auto-create `relationship()` on forward side (Book.author)
- [ ] Auto-create `relationship()` on reverse side (User.books)
- [ ] Handle lazy string references ("User" → User class)
- [ ] Support `related_name` customization
- [ ] Handle `on_delete` behavior in relationships
- [ ] Add tests for relationship loading (lazy/eager)
- [ ] Add tests for cascade delete
- [ ] Document usage in `docs/models-fields-design.md`

**Success Criteria:**
```python
book = Book.objects.get(id=1)
assert isinstance(book.author, User)  # ✅ Works

user = User.objects.get(id=1)
assert isinstance(user.books, QuerySet)  # ✅ Works
assert user.books.count() > 0  # ✅ Works
```

---

#### 1.2 Admin Integration Testing ⚠️ **CRITICAL**
**Priority:** P0  
**Effort:** 1-2 days  
**Owner:** TBD

**Problem:**
- React UI built but never tested end-to-end with FastAPI backend
- No integration tests for admin workflows
- Unknown if CORS, routing, error handling work

**Tasks:**
- [ ] Write integration test: Admin UI loads
- [ ] Write integration test: List view shows data
- [ ] Write integration test: Create new model instance
- [ ] Write integration test: Update existing instance
- [ ] Write integration test: Delete instance
- [ ] Test CORS configuration for dev mode
- [ ] Test API error handling in UI
- [ ] Fix any bugs discovered
- [ ] Document known limitations

**Success Criteria:**
- All CRUD operations work via React UI
- No console errors in browser
- Proper error messages on failures

---

#### 1.3 Admin Security Review ⚠️ **SECURITY**
**Priority:** P0  
**Effort:** 1 day  
**Owner:** TBD

**Problem:**
- Admin API has no authentication
- Anyone can CRUD all models if admin is enabled
- No permission checks

**Tasks:**
- [ ] Audit admin API endpoints for security issues
- [ ] Add authentication requirement (or document its absence)
- [ ] Add warning in docs about securing admin
- [ ] Consider: Disable admin by default in production?
- [ ] Add `@requires_auth` decorator (if auth available)
- [ ] Document admin security model

**Options:**
1. **Block admin entirely until v0.4 auth** (safest)
2. **Add basic HTTP auth** (quick fix)
3. **Document as "dev only"** (risky)

**Recommendation:** Option 3 for v0.3.0, Option 1/2 for v0.3.1

---

### Phase 2: Documentation (2 days) — **SHOULD COMPLETE**

#### 2.1 Deployment Guide
**Priority:** P1  
**Effort:** 1 day

**Content:**
- [ ] Deployment checklist (SECRET_KEY, DEBUG=False, DATABASE_URL)
- [ ] Production ASGI server setup (gunicorn + uvicorn workers)
- [ ] Environment variables and `.env` files
- [ ] Database migration workflow in production
- [ ] Static file serving (when available)
- [ ] Docker example (optional)
- [ ] Cloud platform examples (Heroku, Railway, Fly.io)

---

#### 2.2 Tutorial (Getting Started)
**Priority:** P1  
**Effort:** 1 day

**Content:**
- [ ] "Build your first FastFrame app" tutorial
- [ ] Step-by-step: startproject, models, migrations, endpoints
- [ ] Add admin, create users, customize
- [ ] Deploy to production
- [ ] Reference `examples/todo_app` as working example

---

### Phase 3: Optional Improvements (1-2 weeks) — **NICE TO HAVE**

#### 3.1 ManyToManyField (v0.3.1)
**Priority:** P2  
**Effort:** 1 week

**Implementation:**
```python
tags = fields.ManyToManyField("Tag", related_name="posts")
# Auto-creates join table: posts_tags
# Auto-creates: post.tags.add(tag), post.tags.all(), post.tags.clear()
```

**Tasks:**
- [ ] Design M2M field API
- [ ] Auto-create join table model
- [ ] Add manager methods (add, remove, clear, set)
- [ ] Support `through=` for custom join models
- [ ] Add tests
- [ ] Document usage

---

#### 3.2 Admin Permissions (v0.3.1)
**Priority:** P1 (if auth exists)  
**Effort:** 3-4 days

**Implementation:**
```python
class BookAdmin(ModelAdmin):
    def has_view_permission(self, request):
        return request.user.is_authenticated
    
    def has_add_permission(self, request):
        return request.user.has_permission("books.add")
```

**Tasks:**
- [ ] Add permission hooks to ModelAdmin
- [ ] Add middleware to check user authentication
- [ ] Integrate with User.permissions JSON field
- [ ] Add permission checks to admin API
- [ ] Add tests
- [ ] Document permission system

---

#### 3.3 Admin Search & Filter (v0.3.2)
**Priority:** P2  
**Effort:** 2-3 days

**Implementation:**
```python
class BookAdmin(ModelAdmin):
    search_fields = ["title", "author__name"]
    list_filter = ["published", "category"]
```

**Tasks:**
- [ ] Implement search backend (using QuerySet lookups)
- [ ] Implement filter backend (using Q objects)
- [ ] Update React UI with search bar
- [ ] Update React UI with filter sidebar
- [ ] Add tests
- [ ] Document usage

---

#### 3.4 QuerySet Enhancements (v0.3.2)
**Priority:** P2  
**Effort:** 1 week

**Features:**
- [ ] `select_related("author")` — eager load ForeignKey
- [ ] `prefetch_related("books")` — eager load reverse FK
- [ ] `aggregate(total=Sum("price"))` — aggregation functions
- [ ] `annotate(num_books=Count("books"))` — computed fields
- [ ] `values("title", "author__name")` — dict QuerySet
- [ ] `values_list("title", flat=True)` — list QuerySet

---

## Version Planning

### v0.3.0 (Target: October 2026)
**Theme:** Admin (Preview)

**Scope:**
- ✅ Enhanced models (fields, validation, Q/F objects)
- ⚠️ Relationship auto-generation (BLOCKER)
- ⚠️ Admin (infrastructure, basic CRUD)
- ⚠️ Admin integration testing (BLOCKER)
- ⚠️ Admin security review (BLOCKER)
- ⚠️ Deployment guide
- ⚠️ Tutorial

**Status:** Needs 1 week of work

---

### v0.3.1 (Target: November 2026)
**Theme:** Admin Maturity

**Scope:**
- Admin permissions
- Admin search/filter
- ManyToManyField
- Bug fixes from v0.3.0 feedback

---

### v0.3.2 (Target: December 2026)
**Theme:** Performance & Usability

**Scope:**
- select_related / prefetch_related
- Admin bulk actions
- QuerySet caching
- Performance optimizations

---

### v0.4 (Target: January 2027)
**Theme:** Authentication & Permissions

**Scope:**
- Session authentication
- JWT authentication
- Login/logout views
- Permission middleware
- Password reset flow
- Email verification

---

## Release Strategy

### Option A: Wait for complete v0.3
**Pros:**
- Clean, complete admin experience
- No known critical issues
- Better first impression

**Cons:**
- Delays release by 1-2 weeks
- No feedback until complete
- Risk of scope creep

---

### Option B: Release v0.3.0 as "Preview" (RECOMMENDED)
**Pros:**
- Get feedback sooner
- Iterate based on real usage
- Show progress to community
- Shorter development cycles

**Cons:**
- Rough edges in admin
- May need to backtrack on design

**Approach:**
1. Fix critical blockers (Phase 1)
2. Add clear warnings in docs ("Admin is preview quality")
3. Release as `0.3.0-preview` or `0.3.0` with caveats
4. Iterate quickly to `0.3.1` with fixes

---

### Option C: Split Admin into Separate Package
**Pros:**
- Core framework stays stable
- Admin can iterate independently
- Optional for users

**Cons:**
- More complexity
- Splits ecosystem
- Delays integrated experience

**Recommendation:** Defer to v0.4+ if admin proves unstable

---

## Risk Management

### High-Risk Items

1. **Relationship auto-generation complexity**
   - **Risk:** Breaks existing code, edge cases
   - **Mitigation:** Extensive tests, backward compatibility

2. **Admin security gap**
   - **Risk:** Users deploy insecure admin to production
   - **Mitigation:** Loud warnings, disable by default?

3. **ManyToMany complexity**
   - **Risk:** Underestimate effort, delays release
   - **Mitigation:** Defer to v0.3.1, don't block v0.3.0

---

## Success Metrics

### v0.3.0 Release Goals

**Quality:**
- [ ] All tests passing (195+)
- [ ] No critical bugs
- [ ] Ruff lint clean
- [ ] Documentation complete

**Features:**
- [ ] Relationship auto-generation works
- [ ] Admin CRUD operations work
- [ ] Examples demonstrate all features

**Community:**
- [ ] PyPI package published
- [ ] GitHub release with notes
- [ ] Example projects updated
- [ ] Blog post or announcement

---

## Decision Points

### 1. Admin Security
**Question:** How to handle lack of authentication?

**Options:**
- A. Disable admin by default (safest)
- B. Add basic HTTP auth (quick)
- C. Document as dev-only (risky)
- D. Block until v0.4 (delays)

**Decision:** _TBD_

---

### 2. ManyToMany Timing
**Question:** v0.3.0 or defer to v0.3.1?

**Options:**
- A. Include in v0.3.0 (complete but delayed)
- B. Defer to v0.3.1 (faster release)

**Decision:** _TBD_

---

### 3. Release Strategy
**Question:** Wait for complete or release preview?

**Options:**
- A. Wait 1-2 weeks (Option A)
- B. Release preview now (Option B)
- C. Split admin package (Option C)

**Decision:** _TBD_

---

*Action plan created: 2026-09-23*  
*Review by: Core maintainers*  
*Update after: Each sprint*
