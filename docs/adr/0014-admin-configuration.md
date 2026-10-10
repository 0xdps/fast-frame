# ADR 0014: Admin configuration

## Status

The list slice below is implemented. Fieldsets, custom actions, inlines, and the site features in the later table are not.

## Addition (2026-10-07)

The list slice is in place. The list page renders one control for each `list_filter` field. `search_fields` can follow a relationship, such as `"author__name"`. `list_per_page` defaults to 25. A `ModelAdmin` that sets both `fields` and `exclude` is rejected. `show_in_navigation = False` leaves a model out of the sidebar, and `AuditLog` uses that. The model stays registered and reachable by URL.

Templates are out of scope, so this backlog is not waiting on them. See the Addition on [ADR 0002](0002-fastapi-as-http-layer.md).

## Context

The admin is the bundled React UI plus `ModelAdmin`. Several options in the user's sketch are already wired. Planning the rest means separating what a model looks like from how the admin application behaves, and not adding a parameter for a feature the framework already does.

## Decision

### Two layers

`ModelAdmin` answers "what should this model look like?" `AdminSite` answers "how does the admin application work?"

Quick Access, Recently Viewed, activity history, global search, navigation, authentication, the permission system, theme, and the default page size live on the site. They are not flags repeated on every `ModelAdmin`.

### Already shipped

These stay as they are. The next slices do not re-add them.

| Concern | Today |
| --- | --- |
| Columns | `list_display` |
| Search | `search_fields`, matched with `icontains` |
| Default order | `ordering`, then the model's own ordering |
| Page size | `list_per_page`, read by the list page |
| Form shape | `fields`, `exclude`, and `readonly_fields` are enforced on create and update |
| Permissions | `has_add_permission`, `has_change_permission`, `has_delete_permission`, `has_view_permission`. `enforce_permissions = True` checks `"app.action_model"` for the current user. A static `False` still denies everyone. |
| Relationships | A foreign key shows the related object's label and links to its record. The label is the model's `__str__`, then a name-like field. |
| Relationship input | Every foreign key is a searchable menu backed by `GET /{resource}/choices/{field}`. It does not load the whole table into a dropdown. |
| Bulk delete | The list checkboxes delete the selection. |
| Activity | Create, update, and delete through the admin or the token API write `AuditLog`. The overview shows the latest rows when the user can view that model. |

There is no `permissions` dict, no `object_label`, and no `autocomplete_fields`. The permission flags and `__str__` already cover those, and every foreign key already searches.

### Next slice (shipped 2026-10-07)

This was the plan, and it shipped as written — see the Addition at the top. Left here as the record of what was decided and why.

- Render `list_filter` as controls on the list. The list API already accepts field query params. The controls offer only the fields named in `list_filter`. A filter is a field name. No `DateRangeFilter` class and no custom filter objects in this slice.
- `search_fields` may name a related field, such as `"movie__title"`. That is the same lookup the list search already builds.
- Change the `list_per_page` default from `100` to `25`. The list page already falls back to 25 when the schema omits a size. No page-size menu.
- Reject a `ModelAdmin` that sets both `fields` and `exclude`. One of them describes the form.
- `show_in_navigation = False` keeps a registered model out of the sidebar. Audit-style models are the reason. The model stays reachable by URL for a user who may view it.

`list_display` stays a list of field names. A method or property in that list waits until the schema can describe a column that is not a field.

### Later, still on ModelAdmin

In this order, each one only when the previous list is in use:

1. `fieldsets`: a list of `{title, fields}` groups on the record page. `readonly_fields` still apply inside a group.
2. `actions`: names of methods on the admin class. The list already deletes a selection, so the first new action is a domain method such as `archive(self, queryset)`. `delete_selected` stays the built-in checkbox action and does not have to be listed.
3. `inlines`: a related model edited on the parent's record page. This is also where the record page lists related objects.

`list_per_page_options`, callable `list_display` columns, and custom filter classes stay behind those.

### Site behavior

| Feature | Plan |
| --- | --- |
| Activity log | Keep `AuditLog`. A model does not opt in. A `log_change` hook waits until a project needs to change one entry. |
| Recently viewed | Record it in the browser for every registered model the user opens. No `track_recent_views = True`. An opt-out attribute waits until a model must be skipped. |
| Quick Access | A pin the signed-in user adds. No `quick_access = True`. An opt-out waits until a model must not be pinnable. |
| Global search | One box that queries registered models through each admin's `search_fields`. |
| Navigation groups | Sidebar groups already follow the app label. `navigation_group` waits until a model needs a group other than its app. |

Saved filters, export, and a second permission language are not in this plan. Permissions stay the flags and `enforce_permissions` that already ship.

## Consequences

- New admin work adds a parameter only when a model must differ from the site default.
- The class attributes `fieldsets` and `actions` already exist and do nothing in the UI. The later slices implement those attributes instead of inventing new names.
- This ADR is the admin backlog. Jinja templates and app static files are out of scope.
