# FastFrame Admin - CRUD Implementation Plan

## Current Status
✅ **Implemented:**
- Admin home page with model registry
- List views with search
- Model registration and configuration
- Database session integration
- Sample data display

❌ **Missing:**
- Create (Add) functionality
- Edit (Update) functionality
- Delete functionality
- Form generation from model fields
- Form validation and error display

---

## 1. CREATE (Add) Action

### 1.1 Requirements
- Auto-generate form from model fields
- Handle different field types (CharField, EmailField, BooleanField, ForeignKey, etc.)
- Client-side and server-side validation
- Success/error messages
- Redirect to list or detail view after save

### 1.2 Implementation Steps

#### Step 1: Form Generation System
**File:** `src/fastframe/admin/forms.py`

```python
class ModelForm:
    """Auto-generate HTML form from model fields."""
    
    def __init__(self, model_class, instance=None, data=None):
        self.model = model_class
        self.instance = instance
        self.data = data
        self.errors = {}
    
    def get_fields(self):
        """Get fields to display in form."""
        # Respect ModelAdmin.fields or ModelAdmin.exclude
        # Skip auto-increment PKs
        # Handle field ordering
        pass
    
    def render_field(self, field_name, field):
        """Render HTML for a single field."""
        # Return HTML input based on field type:
        # - CharField -> <input type="text">
        # - EmailField -> <input type="email">
        # - BooleanField -> <input type="checkbox">
        # - TextField -> <textarea>
        # - ForeignKey -> <select> with choices
        # - JSONField -> <textarea> with JSON validation
        pass
    
    def is_valid(self):
        """Validate form data."""
        # Call field.validate() for each field
        # Call model.full_clean() for model-level validation
        pass
    
    def save(self):
        """Save the model instance."""
        # Create or update instance
        # Return saved instance
        pass
```

#### Step 2: Add View (GET)
**File:** `src/fastframe/admin/views.py`

```python
@router.get("/{app_label}/{model_name}/add/", response_class=HTMLResponse)
async def model_add_get(
    request: Request,
    app_label: str,
    model_name: str,
    session=Depends(get_session),
) -> HTMLResponse:
    """Display add/create form."""
    
    model = _find_model(app_label, model_name)
    model_admin = admin_site.get_model_admin(model)
    
    if not model_admin.has_add_permission:
        raise HTTPException(403, "Permission denied")
    
    # Generate empty form
    form = ModelForm(model)
    
    return templates.TemplateResponse(
        request=request,
        name="admin/model_form.html",
        context={
            "model": model,
            "model_admin": model_admin,
            "form": form,
            "title": f"Add {model._meta.get('verbose_name', model.__name__)}",
            "is_add": True,
        },
    )
```

#### Step 3: Add View (POST)
```python
@router.post("/{app_label}/{model_name}/add/")
async def model_add_post(
    request: Request,
    app_label: str,
    model_name: str,
    session=Depends(get_session),
) -> Response:
    """Handle form submission for creating new instance."""
    
    model = _find_model(app_label, model_name)
    model_admin = admin_site.get_model_admin(model)
    
    # Get form data
    form_data = await request.form()
    
    # Set session context
    _session_ctx.set(session)
    
    # Create form with data
    form = ModelForm(model, data=form_data)
    
    if form.is_valid():
        # Save instance
        instance = form.save()
        
        # Success message (flash message)
        return RedirectResponse(
            url=f"/admin/{app_label}/{model_name}/",
            status_code=303
        )
    else:
        # Re-render form with errors
        return templates.TemplateResponse(
            request=request,
            name="admin/model_form.html",
            context={
                "model": model,
                "model_admin": model_admin,
                "form": form,
                "title": f"Add {model._meta.get('verbose_name', model.__name__)}",
                "is_add": True,
            },
        )
```

#### Step 4: Form Template
**File:** `src/fastframe/admin/templates/admin/model_form.html`

```html
<form method="post" class="space-y-6">
    {% if form.errors %}
    <div class="bg-red-50 border-l-4 border-red-400 p-4 rounded">
        <h3 class="text-sm font-medium text-red-800">Please correct the errors below:</h3>
        <ul class="mt-2 text-sm text-red-700">
            {% for field, errors in form.errors.items() %}
            <li>{{ field }}: {{ errors }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    {% for field_name, field_html in form.render_fields() %}
    <div class="form-field">
        <label class="block text-sm font-medium text-gray-700 mb-2">
            {{ field.verbose_name }}
            {% if field.required %}<span class="text-red-500">*</span>{% endif %}
        </label>
        {{ field_html | safe }}
        {% if field.help_text %}
        <p class="mt-1 text-sm text-gray-500">{{ field.help_text }}</p>
        {% endif %}
    </div>
    {% endfor %}
    
    <div class="flex justify-end space-x-3">
        <a href="/admin/{{ app_label }}/{{ model_name }}/" 
           class="bg-gray-300 hover:bg-gray-400 px-6 py-2 rounded-lg">
            Cancel
        </a>
        <button type="submit" 
                class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg">
            Save
        </button>
    </div>
</form>
```

#### Step 5: Widget System
**File:** `src/fastframe/admin/widgets.py`

```python
class Widget:
    """Base widget for rendering form fields."""
    
    def render(self, name, value, attrs=None):
        """Render HTML for the widget."""
        pass

class TextInput(Widget):
    """<input type="text">"""
    pass

class EmailInput(Widget):
    """<input type="email">"""
    pass

class CheckboxInput(Widget):
    """<input type="checkbox">"""
    pass

class Select(Widget):
    """<select> dropdown."""
    
    def __init__(self, choices):
        self.choices = choices
    
    def render(self, name, value, attrs=None):
        # Render <select><option>...</option></select>
        pass

class ForeignKeyWidget(Select):
    """Select widget for ForeignKey fields."""
    
    def __init__(self, model):
        # Query all instances of related model
        # Build choices from queryset
        pass
```

### 1.3 Field Type Mapping
```python
FIELD_WIDGET_MAP = {
    "CharField": TextInput,
    "EmailField": EmailInput,
    "URLField": TextInput,
    "TextField": Textarea,
    "IntegerField": NumberInput,
    "BooleanField": CheckboxInput,
    "DateField": DateInput,
    "DateTimeField": DateTimeInput,
    "UUIDField": TextInput(attrs={"readonly": True}),  # Auto-generated
    "JSONField": Textarea(attrs={"rows": 5}),
    "ForeignKey": ForeignKeyWidget,
}
```

### 1.4 Testing Checklist
- [ ] Can create user with all field types
- [ ] Email validation works
- [ ] UUID is auto-generated
- [ ] ForeignKey dropdown shows all options
- [ ] Boolean checkbox defaults correctly
- [ ] JSON field accepts valid JSON
- [ ] Error messages display for invalid data
- [ ] Success redirect to list view
- [ ] Model.clean() validation runs
- [ ] Database constraints enforced (unique, null, etc.)

---

## 2. UPDATE (Edit) Action

### 2.1 Requirements
- Pre-populate form with existing data
- Same form generation as Create
- Handle partial updates
- Prevent concurrent edit conflicts (optimistic locking)
- "Save and continue editing" option

### 2.2 Implementation Steps

#### Step 1: Edit View (GET)
```python
@router.get("/{app_label}/{model_name}/{pk}/change/", response_class=HTMLResponse)
async def model_change_get(
    request: Request,
    app_label: str,
    model_name: str,
    pk: str,
    session=Depends(get_session),
) -> HTMLResponse:
    """Display edit form for existing instance."""
    
    model = _find_model(app_label, model_name)
    model_admin = admin_site.get_model_admin(model)
    
    if not model_admin.has_change_permission:
        raise HTTPException(403, "Permission denied")
    
    # Set session context
    _session_ctx.set(session)
    
    # Get instance
    instance = model.objects.get(pk)
    if not instance:
        raise HTTPException(404, "Object not found")
    
    # Generate form with instance data
    form = ModelForm(model, instance=instance)
    
    return templates.TemplateResponse(
        request=request,
        name="admin/model_form.html",
        context={
            "model": model,
            "model_admin": model_admin,
            "form": form,
            "instance": instance,
            "title": f"Change {model._meta.get('verbose_name', model.__name__)}: {instance}",
            "is_add": False,
        },
    )
```

#### Step 2: Edit View (POST)
```python
@router.post("/{app_label}/{model_name}/{pk}/change/")
async def model_change_post(
    request: Request,
    app_label: str,
    model_name: str,
    pk: str,
    session=Depends(get_session),
) -> Response:
    """Handle form submission for updating instance."""
    
    model = _find_model(app_label, model_name)
    model_admin = admin_site.get_model_admin(model)
    
    # Get form data
    form_data = await request.form()
    
    # Set session context
    _session_ctx.set(session)
    
    # Get instance
    instance = model.objects.get(pk)
    if not instance:
        raise HTTPException(404, "Object not found")
    
    # Create form with instance and data
    form = ModelForm(model, instance=instance, data=form_data)
    
    if form.is_valid():
        # Update instance
        updated_instance = form.save()
        
        # Check for "save and continue editing" button
        if "_continue" in form_data:
            return RedirectResponse(
                url=f"/admin/{app_label}/{model_name}/{pk}/change/",
                status_code=303
            )
        else:
            # Redirect to list
            return RedirectResponse(
                url=f"/admin/{app_label}/{model_name}/",
                status_code=303
            )
    else:
        # Re-render form with errors
        return templates.TemplateResponse(
            request=request,
            name="admin/model_form.html",
            context={
                "model": model,
                "model_admin": model_admin,
                "form": form,
                "instance": instance,
                "title": f"Change {model._meta.get('verbose_name', model.__name__)}: {instance}",
                "is_add": False,
            },
        )
```

#### Step 3: Form Updates
Add multiple submit buttons:
```html
<div class="flex justify-between items-center border-t pt-6">
    <a href="/admin/{{ app_label }}/{{ model_name }}/" 
       class="text-gray-600 hover:text-gray-900">
        ← Back to list
    </a>
    <div class="flex space-x-3">
        {% if not is_add %}
        <button type="submit" name="_continue" value="1"
                class="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg">
            Save and continue editing
        </button>
        {% endif %}
        <button type="submit" name="_save" value="1"
                class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg">
            Save
        </button>
    </div>
</div>
```

### 2.3 Readonly Fields
```python
class ModelAdmin:
    readonly_fields = []  # Fields that can't be edited
    
    def get_readonly_fields(self, request, obj=None):
        """Return readonly fields for this instance."""
        # obj is None for add, populated for change
        if obj:
            # Maybe make id readonly for existing objects
            return self.readonly_fields + ["id"]
        return self.readonly_fields
```

Render readonly fields as disabled inputs:
```html
{% if field.readonly %}
<input type="text" value="{{ field.value }}" disabled 
       class="bg-gray-100 border border-gray-300 rounded px-3 py-2">
{% else %}
{{ field.render() }}
{% endif %}
```

### 2.4 Testing Checklist
- [ ] Form pre-populated with existing values
- [ ] Can update individual fields
- [ ] Validation works on update
- [ ] ForeignKey changes work
- [ ] "Save and continue editing" works
- [ ] Readonly fields are disabled
- [ ] Auto-increment PKs are readonly
- [ ] Unique constraint violations handled
- [ ] Optimistic locking (if implemented)

---

## 3. DELETE Action

### 3.1 Requirements
- Confirmation page before delete
- Show what will be deleted (cascade preview)
- Handle CASCADE, SET_NULL, RESTRICT behaviors
- Bulk delete from list view
- Soft delete option (future)

### 3.2 Implementation Steps

#### Step 1: Delete Confirmation View (GET)
```python
@router.get("/{app_label}/{model_name}/{pk}/delete/", response_class=HTMLResponse)
async def model_delete_get(
    request: Request,
    app_label: str,
    model_name: str,
    pk: str,
    session=Depends(get_session),
) -> HTMLResponse:
    """Display delete confirmation page."""
    
    model = _find_model(app_label, model_name)
    model_admin = admin_site.get_model_admin(model)
    
    if not model_admin.has_delete_permission:
        raise HTTPException(403, "Permission denied")
    
    # Set session context
    _session_ctx.set(session)
    
    # Get instance
    instance = model.objects.get(pk)
    if not instance:
        raise HTTPException(404, "Object not found")
    
    # Find related objects that will be affected
    related_objects = _get_related_objects(instance)
    
    return templates.TemplateResponse(
        request=request,
        name="admin/model_delete_confirm.html",
        context={
            "model": model,
            "model_admin": model_admin,
            "instance": instance,
            "related_objects": related_objects,
            "title": f"Delete {model._meta.get('verbose_name', model.__name__)}: {instance}",
        },
    )
```

#### Step 2: Find Related Objects
```python
def _get_related_objects(instance):
    """Find objects that will be affected by deletion.
    
    Returns dict of related model -> list of instances.
    """
    related = {}
    
    # Inspect ForeignKey fields that reference this model
    # Check on_delete behavior:
    # - CASCADE: will be deleted
    # - SET_NULL: will be set to NULL
    # - RESTRICT: prevent deletion
    # - SET_DEFAULT: will be set to default value
    
    for related_model in _get_models_with_fk_to(instance.__class__):
        # Query instances that reference this one
        # Group by on_delete behavior
        pass
    
    return related
```

#### Step 3: Delete View (POST)
```python
@router.post("/{app_label}/{model_name}/{pk}/delete/")
async def model_delete_post(
    request: Request,
    app_label: str,
    model_name: str,
    pk: str,
    session=Depends(get_session),
) -> Response:
    """Handle deletion of instance."""
    
    model = _find_model(app_label, model_name)
    model_admin = admin_site.get_model_admin(model)
    
    if not model_admin.has_delete_permission:
        raise HTTPException(403, "Permission denied")
    
    # Set session context
    _session_ctx.set(session)
    
    # Get instance
    instance = model.objects.get(pk)
    if not instance:
        raise HTTPException(404, "Object not found")
    
    # Check for RESTRICT constraints
    # This should be done at DB level but we can check here too
    
    # Delete instance (CASCADE will handle related objects)
    session.delete(instance)
    session.commit()
    
    # Success message
    return RedirectResponse(
        url=f"/admin/{app_label}/{model_name}/",
        status_code=303
    )
```

#### Step 4: Delete Confirmation Template
**File:** `src/fastframe/admin/templates/admin/model_delete_confirm.html`

```html
<div class="max-w-4xl mx-auto">
    <div class="bg-white rounded-lg shadow-md p-8">
        <h2 class="text-2xl font-bold mb-6 text-red-600">
            Are you sure?
        </h2>
        
        <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
            <p class="text-sm text-yellow-800">
                Are you sure you want to delete 
                <strong>{{ instance }}</strong>?
                This action cannot be undone.
            </p>
        </div>
        
        {% if related_objects %}
        <div class="mb-6">
            <h3 class="text-lg font-semibold mb-3 text-gray-800">
                The following related objects will be affected:
            </h3>
            
            {% for related_model, objects in related_objects.items() %}
            <div class="mb-4">
                <h4 class="font-medium text-gray-700">{{ related_model.verbose_name_plural }}:</h4>
                <ul class="ml-6 mt-2 space-y-1">
                    {% for obj in objects %}
                    <li class="text-sm text-gray-600">
                        <span class="font-mono bg-gray-100 px-2 py-1 rounded">
                            {{ obj }}
                        </span>
                        <span class="text-red-500 ml-2">will be deleted</span>
                    </li>
                    {% endfor %}
                </ul>
            </div>
            {% endfor %}
        </div>
        {% endif %}
        
        <form method="post" class="flex justify-between items-center border-t pt-6">
            <a href="/admin/{{ app_label }}/{{ model_name }}/" 
               class="bg-gray-300 hover:bg-gray-400 text-gray-800 px-6 py-2 rounded-lg">
                No, take me back
            </a>
            <button type="submit" 
                    class="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg">
                Yes, I'm sure - Delete
            </button>
        </form>
    </div>
</div>
```

### 3.3 Bulk Delete (from list view)
```python
@router.post("/{app_label}/{model_name}/bulk-delete/")
async def model_bulk_delete(
    request: Request,
    app_label: str,
    model_name: str,
    session=Depends(get_session),
) -> Response:
    """Handle bulk deletion of selected instances."""
    
    form_data = await request.form()
    selected_ids = form_data.getlist("selected")
    
    if not selected_ids:
        # No selection
        return RedirectResponse(
            url=f"/admin/{app_label}/{model_name}/",
            status_code=303
        )
    
    model = _find_model(app_label, model_name)
    model_admin = admin_site.get_model_admin(model)
    
    if not model_admin.has_delete_permission:
        raise HTTPException(403, "Permission denied")
    
    # Set session context
    _session_ctx.set(session)
    
    # Delete selected instances
    for pk in selected_ids:
        instance = model.objects.get(pk)
        if instance:
            session.delete(instance)
    
    session.commit()
    
    return RedirectResponse(
        url=f"/admin/{app_label}/{model_name}/",
        status_code=303
    )
```

Add checkboxes to list view:
```html
<table class="min-w-full">
    <thead>
        <tr>
            <th><input type="checkbox" id="select-all"></th>
            <!-- other headers -->
        </tr>
    </thead>
    <tbody>
        {% for row in table_rows %}
        <tr>
            <td><input type="checkbox" name="selected" value="{{ row.pk }}"></td>
            <!-- other columns -->
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="p-4 border-t">
    <select name="action" class="border rounded px-3 py-2">
        <option value="">Select action</option>
        <option value="delete">Delete selected</option>
    </select>
    <button type="submit" class="bg-gray-600 text-white px-4 py-2 rounded ml-2">
        Go
    </button>
</div>
```

### 3.4 Testing Checklist
- [ ] Delete confirmation page shows
- [ ] Related objects listed (CASCADE)
- [ ] Can cancel deletion
- [ ] Deletion removes from database
- [ ] CASCADE deletes work correctly
- [ ] RESTRICT prevents deletion
- [ ] SET_NULL updates related objects
- [ ] Bulk delete works for multiple items
- [ ] Permission check works
- [ ] Redirect to list after delete

---

## 4. Flash Messages System

### 4.1 Requirements
Users need feedback after actions:
- "User 'alice' was added successfully"
- "Post 'Getting Started' was changed successfully"
- "3 posts were deleted"
- "Error: Email already exists"

### 4.2 Implementation
```python
from starlette.middleware.sessions import SessionMiddleware

# Add to FastAPI app
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")

def add_message(request: Request, level: str, message: str):
    """Add flash message to session."""
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append({"level": level, "text": message})

def get_messages(request: Request):
    """Get and clear flash messages."""
    messages = request.session.pop("messages", [])
    return messages
```

Template:
```html
{% for message in messages %}
<div class="alert alert-{{ message.level }}">
    {{ message.text }}
</div>
{% endfor %}
```

---

## 5. Priority Implementation Order

### Phase 1: Core CRUD (Week 1)
1. **Day 1-2:** Form generation system
   - ModelForm class
   - Widget system
   - Field rendering

2. **Day 3:** Create (Add) action
   - GET view with empty form
   - POST view with validation
   - Success redirect

3. **Day 4:** Update (Edit) action
   - GET view with pre-populated form
   - POST view with validation
   - "Save and continue editing"

4. **Day 5:** Delete action
   - Confirmation page
   - POST delete handler
   - Related objects preview

### Phase 2: Polish (Week 2)
5. **Day 1:** Flash messages
6. **Day 2:** Readonly fields
7. **Day 3:** Bulk delete
8. **Day 4:** Error handling improvements
9. **Day 5:** Testing and bug fixes

### Phase 3: Advanced Features (Week 3)
10. Inline editing (edit from list view)
11. Custom actions (beyond delete)
12. File upload widget
13. Date/time pickers
14. Autocomplete for ForeignKeys

---

## 6. Testing Strategy

### Unit Tests
- `tests/test_admin_forms.py` - Form generation and validation
- `tests/test_admin_widgets.py` - Widget rendering
- `tests/test_admin_crud.py` - CRUD operations

### Integration Tests
- Create user through admin
- Edit post through admin
- Delete comment through admin
- Bulk delete multiple items
- ForeignKey relationships work
- Validation errors display

### Manual Testing Checklist
- [ ] All field types render correctly
- [ ] Validation messages are clear
- [ ] Success messages display
- [ ] Navigation works (back to list, continue editing)
- [ ] Related objects shown before delete
- [ ] Bulk actions work
- [ ] Forms work on mobile (responsive)

---

## 7. Additional Considerations

### Security
- [ ] CSRF protection on POST forms
- [ ] Permission checks on all actions
- [ ] SQL injection prevention (SQLAlchemy handles)
- [ ] XSS prevention in templates (Jinja2 escapes)

### Performance
- [ ] ForeignKey dropdowns: limit to reasonable number or add search
- [ ] Pagination for related objects in delete confirm
- [ ] Lazy load ForeignKey options with autocomplete

### UX Improvements
- [ ] Keyboard shortcuts (Ctrl+S to save)
- [ ] Unsaved changes warning
- [ ] Field focus on first error
- [ ] Remember form position after validation error
- [ ] Auto-save draft (localStorage)

---

## Files to Create/Modify

### New Files
- `src/fastframe/admin/forms.py` - Form generation
- `src/fastframe/admin/widgets.py` - Form widgets
- `src/fastframe/admin/messages.py` - Flash messages
- `src/fastframe/admin/templates/admin/model_delete_confirm.html`
- `tests/test_admin_forms.py`
- `tests/test_admin_crud.py`

### Modified Files
- `src/fastframe/admin/views.py` - Add POST handlers
- `src/fastframe/admin/templates/admin/model_form.html` - Complete form template
- `src/fastframe/admin/templates/admin/model_list.html` - Add bulk actions
- `src/fastframe/admin/templates/admin/base.html` - Add message display
- `src/fastframe/admin/site.py` - Add form-related methods to ModelAdmin

---

## Success Criteria

✅ Admin is "production-ready" when:
1. Can create new instances of any model
2. Can edit existing instances
3. Can delete instances with confirmation
4. Forms validate correctly
5. Error messages are clear and helpful
6. Success feedback is provided
7. ForeignKey fields work as dropdowns
8. All field types are supported
9. Bulk delete works
10. Responsive on mobile devices
