# Customizing the admin UI

`python manage.py startadmin` copies the React Admin project into `admin-ui/`
(pass another directory as the first argument, or `--force` to replace it).

## What to edit

| File | Change |
| --- | --- |
| `src/theme.ts` | Colors, type, component defaults. `theme` (light) and `darkTheme` are both exported and passed to `<Admin>`, so the dark-mode toggle in the user menu works out of the box. |
| `src/layout.tsx` | Sidebar (search box, models grouped by app, collapsible sections) and the app bar (delegates the user menu to `userMenu.tsx`) |
| `src/dashboard.tsx` | The "Overview" landing page — deliberately mostly empty, just a greeting plus `activity.tsx`'s recent-activity panel |
| `src/activity.tsx` | Recent-activity panel, reads the `AuditLog` model (skips rendering if the current user can't view it) |
| `src/userMenu.tsx` | Top-right avatar menu: profile link, dark-mode toggle, log out |
| `src/currentUser.ts` | `useCurrentUser()` — fetches `GET /me` for the user menu |
| `src/index.css` | Layout of the dashboard, sidebar, user menu, and user profile |
| `src/users.tsx` | Profile page and change-password form. Used when the model name is `User` or `SimpleUser`. |
| `src/resources.tsx` | Generated list columns and form inputs |
| `src/App.tsx` | Resource registration. The default router is a hash router, so routes look like `/admin/#/user`. |

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
`src/users.tsx`.
