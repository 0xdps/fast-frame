# Customizing the admin UI

`python manage.py startadmin` copies the admin UI into `admin-ui/`
(pass another directory as the first argument, or `--force` to replace it).

## Sidebar

The sidebar does not collapse. Every model uses the same list icon, so a
narrow icon rail cannot tell one model from another. The sidebar stays at
its open width and shows each model's name. There is no collapse control.

The FastFrame header at the top of the sidebar opens the dashboard
(Overview). App groups inside the sidebar can still be collapsed; those
groups keep the model names when they are open. Model search lives in the
sidebar.

See [ADR 0011](adr/0011-admin-sidebar-stays-expanded.md).

## What to edit

| File | Change |
| --- | --- |
| `src/shell.tsx` | Sidebar and top bar. The sidebar stays expanded; see [Sidebar](#sidebar). |
| `src/pages/overview.tsx` | The Overview page: a short greeting and recent activity when the current user can view `AuditLog`. |
| `src/pages/resource-list.tsx` | Schema-driven list: search, sort, pagination, bulk delete. |
| `src/pages/resource-form.tsx` | Schema-driven create and edit forms, including the user profile and change-password panel. |
| `src/admin-state.ts` | Theme and refresh. Dark mode is a `data-theme` attribute on `<html>`. |
| `src/currentUser.ts` | `useCurrentUser()` — fetches `GET /me` for the user menu. |
| `src/index.css` | Theme tokens, the fixed app shell, and scrollbars. |
| `src/App.tsx` | Loads `GET /api/admin/schema` and the hash routes (`/admin/#/user`). |

The UI loads `GET /api/admin/schema` and builds a resource per registered
model. Register models in Python with `admin_site.register`; do not hard-code
them in React unless you want a one-off view.

## Develop and ship

```text
cd admin-ui
npm install
npm run dev
npm run build
```

Set `ADMIN_MODE = "custom"` so FastAPI serves `admin-ui/dist` at
`ADMIN_PREFIX`. See [admin-deployment.md](admin-deployment.md).

## API URL and base path

| Variable | When |
| --- | --- |
| `VITE_API_URL` | Override the API origin. Dev default is `http://127.0.0.1:8000/api/admin`. Production default is `/api/admin`. |
| `VITE_BASE` | Override the Vite base. Production default is `/admin/`. |

A UI hosted on another domain:

```text
VITE_BASE=/ VITE_API_URL=https://api.example.com/api/admin npm run build
```

Allow that origin in CORS on the API.

## User profile

The profile view is full width, with a header and a separate change-password
form. Password fields are `write_only`: they appear on create, stay out of
API responses, and are updated through the change-password action on edit.

To give another model that profile, match it in `isUserModel()` in
`src/lib/format.ts`.
