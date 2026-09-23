# FastFrame Admin - REST API + React Admin Architecture

## Decision: Switch from SSR to CSR with REST API

### Context
We initially chose SSR (ADR 0007) but realized:
- Modern admin panels (React Admin, Refine) are mature and feature-rich
- SSR requires rebuilding all UI components from scratch
- REST API is more reusable (web, mobile, CLI)
- Better developer experience with React ecosystem

### Decision
Build a **JSON REST API** for admin operations, consumed by **React Admin** (or similar).

---

## Architecture

### Backend: FastFrame Admin API
**Technology:** FastAPI + SQLAlchemy (existing)
**Purpose:** Provide REST endpoints for CRUD operations

```
/api/admin/
├── /models/                    # List all registered models
├── /{model}/                   # List instances
├── /{model}/{id}/              # Get/Update/Delete instance
├── /{model}/schema/            # Get model schema (fields, types)
└── /{model}/choices/           # Get choices for ForeignKey fields
```

### Frontend: React Admin SPA
**Technology:** Vite + React + TypeScript + React Admin
**Purpose:** Beautiful, interactive admin interface

```
admin-ui/
├── src/
│   ├── App.tsx                 # React Admin setup
│   ├── dataProvider.ts         # FastFrame API adapter
│   ├── resources/              # Model-specific customizations
│   └── components/             # Custom components
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## Phase 1: Admin REST API (Backend)

### File: `src/fastframe/admin/api.py`

```python
"""Admin REST API for CRUD operations."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Optional

from fastframe.admin.site import admin_site
from fastframe.db.session import get_session

router = APIRouter(prefix="/api/admin", tags=["admin-api"])


# === Schema Endpoints ===

@router.get("/models")
async def list_models():
    """Get all registered models with metadata."""
    registry = admin_site.get_registry()
    
    models = []
    for model, model_admin in registry.items():
        models.append({
            "name": model.__name__,
            "label": model._meta.get("verbose_name", model.__name__),
            "labelPlural": model._meta.get("verbose_name_plural", f"{model.__name__}s"),
            "appLabel": model._meta.get("app_label", "app"),
            "listDisplay": model_admin.list_display,
            "searchFields": model_admin.search_fields,
            "canCreate": model_admin.has_add_permission,
            "canEdit": model_admin.has_change_permission,
            "canDelete": model_admin.has_delete_permission,
        })
    
    return {"models": models}


@router.get("/models/{model_name}/schema")
async def get_model_schema(model_name: str):
    """Get field schema for a model."""
    model = _find_model_by_name(model_name)
    
    fields = []
    for field_name, field in model._meta.get("fields", {}).items():
        field_schema = {
            "name": field_name,
            "type": field.__class__.__name__,
            "label": field.verbose_name or field_name.replace("_", " ").title(),
            "required": not field.null and field.default is field.NOT_PROVIDED,
            "helpText": field.help_text,
        }
        
        # Add type-specific metadata
        if hasattr(field, "max_length"):
            field_schema["maxLength"] = field.max_length
        
        if hasattr(field, "choices") and field.choices:
            field_schema["choices"] = [
                {"value": v, "label": l} for v, l in field.choices
            ]
        
        if hasattr(field, "to"):  # ForeignKey
            field_schema["reference"] = field.to
            field_schema["relationshipName"] = field.relationship_name
        
        fields.append(field_schema)
    
    return {"fields": fields}


# === CRUD Endpoints ===

@router.get("/models/{model_name}")
async def list_instances(
    model_name: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    search: str = "",
    sort_field: str = "",
    sort_order: str = "ASC",
    session=Depends(get_session),
):
    """List model instances with pagination and search."""
    model = _find_model_by_name(model_name)
    model_admin = admin_site.get_model_admin(model)
    
    # Set session context
    from fastframe.db.session import _session_ctx
    _session_ctx.set(session)
    
    # Get queryset
    qs = model_admin.get_queryset(None)
    
    # Apply search
    if search:
        qs = model_admin.get_search_results(qs, search)
    
    # Get total count
    total = len(list(qs))
    
    # Apply sorting (TODO: implement in QuerySet)
    
    # Apply pagination
    offset = (page - 1) * per_page
    results = list(qs)[offset:offset + per_page]
    
    # Serialize instances
    data = []
    for instance in results:
        item = {"id": instance.id if hasattr(instance, "id") else None}
        
        # Get all field values
        for field_name in model._meta.get("fields", {}).keys():
            value = getattr(instance, field_name, None)
            
            # Handle special types
            if hasattr(value, "isoformat"):  # datetime/date
                value = value.isoformat()
            elif hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, type(None))):
                # ForeignKey or related object
                value = {"id": value.id if hasattr(value, "id") else None, "display": str(value)}
            
            item[field_name] = value
        
        data.append(item)
    
    return {
        "data": data,
        "total": total,
        "page": page,
        "perPage": per_page,
    }


@router.get("/models/{model_name}/{id}")
async def get_instance(
    model_name: str,
    id: str,
    session=Depends(get_session),
):
    """Get a single instance."""
    model = _find_model_by_name(model_name)
    
    from fastframe.db.session import _session_ctx
    _session_ctx.set(session)
    
    instance = model.objects.get(id)
    if not instance:
        raise HTTPException(404, "Not found")
    
    # Serialize instance (same as list_instances)
    data = {"id": instance.id if hasattr(instance, "id") else None}
    for field_name in model._meta.get("fields", {}).keys():
        value = getattr(instance, field_name, None)
        if hasattr(value, "isoformat"):
            value = value.isoformat()
        elif hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, type(None))):
            value = {"id": value.id if hasattr(value, "id") else None, "display": str(value)}
        data[field_name] = value
    
    return {"data": data}


@router.post("/models/{model_name}")
async def create_instance(
    model_name: str,
    data: dict[str, Any],
    session=Depends(get_session),
):
    """Create a new instance."""
    model = _find_model_by_name(model_name)
    model_admin = admin_site.get_model_admin(model)
    
    if not model_admin.has_add_permission:
        raise HTTPException(403, "Permission denied")
    
    from fastframe.db.session import _session_ctx
    _session_ctx.set(session)
    
    try:
        # Create instance
        instance = model(**data)
        
        # Validate
        instance.full_clean()
        
        # Save
        instance.save()
        
        return {"data": {"id": instance.id}, "message": f"{model._meta.get('verbose_name', model.__name__)} created successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))


@router.put("/models/{model_name}/{id}")
async def update_instance(
    model_name: str,
    id: str,
    data: dict[str, Any],
    session=Depends(get_session),
):
    """Update an existing instance."""
    model = _find_model_by_name(model_name)
    model_admin = admin_site.get_model_admin(model)
    
    if not model_admin.has_change_permission:
        raise HTTPException(403, "Permission denied")
    
    from fastframe.db.session import _session_ctx
    _session_ctx.set(session)
    
    instance = model.objects.get(id)
    if not instance:
        raise HTTPException(404, "Not found")
    
    try:
        # Update fields
        for field_name, value in data.items():
            if hasattr(instance, field_name):
                setattr(instance, field_name, value)
        
        # Validate
        instance.full_clean()
        
        # Save
        instance.save()
        
        return {"data": {"id": instance.id}, "message": f"{model._meta.get('verbose_name', model.__name__)} updated successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))


@router.delete("/models/{model_name}/{id}")
async def delete_instance(
    model_name: str,
    id: str,
    session=Depends(get_session),
):
    """Delete an instance."""
    model = _find_model_by_name(model_name)
    model_admin = admin_site.get_model_admin(model)
    
    if not model_admin.has_delete_permission:
        raise HTTPException(403, "Permission denied")
    
    from fastframe.db.session import _session_ctx
    _session_ctx.set(session)
    
    instance = model.objects.get(id)
    if not instance:
        raise HTTPException(404, "Not found")
    
    try:
        session.delete(instance)
        session.commit()
        
        return {"message": f"{model._meta.get('verbose_name', model.__name__)} deleted successfully"}
    except Exception as e:
        raise HTTPException(400, str(e))


# === Helper Functions ===

def _find_model_by_name(model_name: str):
    """Find model by name across all registered models."""
    registry = admin_site.get_registry()
    
    for model in registry:
        if model.__name__.lower() == model_name.lower():
            return model
    
    raise HTTPException(404, f"Model {model_name} not found")
```

### Update `src/fastframe/admin/__init__.py`

```python
from fastframe.admin.api import router as admin_api_router
from fastframe.admin.site import AdminSite, ModelAdmin, admin_site
from fastframe.admin.views import get_admin_router

__all__ = [
    "AdminSite",
    "ModelAdmin",
    "admin_site",
    "get_admin_router",  # SSR views (legacy/optional)
    "admin_api_router",  # NEW: REST API
]
```

---

## Phase 2: React Admin Frontend

### Setup

```bash
cd examples/blog_app
npm create vite@latest admin-ui -- --template react-ts
cd admin-ui
npm install react-admin ra-data-simple-rest
```

### File: `admin-ui/src/App.tsx`

```typescript
import { Admin, Resource, ListGuesser, EditGuesser } from 'react-admin';
import fastFrameDataProvider from './dataProvider';

const dataProvider = fastFrameDataProvider('http://localhost:8000/api/admin');

const App = () => (
  <Admin dataProvider={dataProvider}>
    {/* Auto-discovered from API */}
    <Resource name="SimpleUser" />
    <Resource name="Post" />
    <Resource name="Category" />
    <Resource name="Tag" />
    <Resource name="Comment" />
  </Admin>
);

export default App;
```

### File: `admin-ui/src/dataProvider.ts`

```typescript
import { DataProvider, fetchUtils } from 'react-admin';

const fastFrameDataProvider = (apiUrl: string): DataProvider => {
  const httpClient = fetchUtils.fetchJson;

  return {
    getList: async (resource, params) => {
      const { page, perPage } = params.pagination;
      const { field, order } = params.sort;
      const query = {
        page,
        per_page: perPage,
        sort_field: field,
        sort_order: order,
        search: params.filter.q || '',
      };

      const url = `${apiUrl}/models/${resource}?${new URLSearchParams(query)}`;
      const { json } = await httpClient(url);

      return {
        data: json.data,
        total: json.total,
      };
    },

    getOne: async (resource, params) => {
      const url = `${apiUrl}/models/${resource}/${params.id}`;
      const { json } = await httpClient(url);
      return { data: json.data };
    },

    create: async (resource, params) => {
      const url = `${apiUrl}/models/${resource}`;
      const { json } = await httpClient(url, {
        method: 'POST',
        body: JSON.stringify(params.data),
      });
      return { data: json.data };
    },

    update: async (resource, params) => {
      const url = `${apiUrl}/models/${resource}/${params.id}`;
      const { json } = await httpClient(url, {
        method: 'PUT',
        body: JSON.stringify(params.data),
      });
      return { data: json.data };
    },

    delete: async (resource, params) => {
      const url = `${apiUrl}/models/${resource}/${params.id}`;
      await httpClient(url, { method: 'DELETE' });
      return { data: params.previousData };
    },

    // ... other methods
  };
};

export default fastFrameDataProvider;
```

---

## Benefits of This Approach

### ✅ Immediate Benefits
1. **React Admin provides out-of-the-box:**
   - Complete CRUD interface
   - Search and filters
   - Pagination
   - Sorting
   - Validation
   - Form generation
   - Relationship handling
   - Bulk actions
   - Export functionality
   - Responsive design
   - Accessibility

2. **Customizable:**
   - Override any component
   - Custom themes
   - Custom actions
   - Custom fields

3. **Reusable API:**
   - Mobile app can use same API
   - CLI tools can use same API
   - Third-party integrations

### ✅ Less Code to Maintain
- **SSR Approach:** ~3000+ lines of forms, widgets, templates
- **REST API + React Admin:** ~500 lines (just API endpoints)

### ✅ Better Performance
- SPA: No full page reloads
- Optimistic updates
- Client-side caching
- Better perceived performance

---

## Comparison: SSR vs CSR

| Feature | SSR (Current) | REST API + React Admin |
|---------|---------------|------------------------|
| Development Time | ~3-4 weeks | ~1 week |
| Code to Maintain | ~3000+ lines | ~500 lines (API only) |
| User Experience | Page reloads | Instant, no reloads |
| Mobile Support | Limited | Excellent |
| Customization | Template-based | Component-based |
| Ecosystem | Build everything | Reuse thousands of components |
| API Reusability | None (tied to HTML) | Reusable for any client |
| Real-time Updates | Hard | Easy (WebSockets) |
| Offline Support | No | Yes (PWA) |

---

## Migration Path

### Step 1: Build REST API (This Sprint)
- Implement `/api/admin/` endpoints
- Test with curl/Postman
- Document API

### Step 2: Build React Admin (Next Sprint)
- Set up Vite + React
- Configure React Admin
- Connect to FastFrame API
- Customize as needed

### Step 3: Deprecate SSR Views (Optional)
- Keep SSR as fallback for simple cases
- Or remove entirely

---

## Alternative React Admin Libraries

### Option 1: React Admin (Recommended)
- **Pros:** Most mature, largest community, extensive features
- **Cons:** Learning curve
- **Website:** https://marmelab.com/react-admin/

### Option 2: Refine
- **Pros:** More flexible, TypeScript-first, headless architecture
- **Cons:** Smaller community
- **Website:** https://refine.dev/

### Option 3: AdminJS
- **Pros:** Node.js focused, good for JavaScript backends
- **Cons:** Less React-focused
- **Website:** https://adminjs.co/

### Recommendation: **React Admin**
- Most battle-tested
- Best documentation
- Largest ecosystem of extensions

---

## Implementation Timeline

### Week 1: REST API
- Day 1-2: Core CRUD endpoints
- Day 3: Schema introspection endpoints
- Day 4: Testing and documentation
- Day 5: CORS, auth, error handling

### Week 2: React Admin
- Day 1: Project setup, basic integration
- Day 2: Custom data provider
- Day 3: Resource definitions
- Day 4: Customizations (themes, layouts)
- Day 5: Testing and polish

### Week 3: Advanced Features
- Day 1-2: File uploads
- Day 3: Real-time updates
- Day 4: Custom actions
- Day 5: Deployment

---

## Decision: Adopt REST API + React Admin

**Status:** ✅ Approved

**Rationale:**
1. Faster development (1 week vs 3-4 weeks)
2. Better UX (SPA vs page reloads)
3. Less code to maintain (500 vs 3000+ lines)
4. Reusable API for mobile, CLI, integrations
5. Leverage mature React ecosystem
6. Better long-term sustainability

**Supersedes:** ADR 0007 (SSR approach)
