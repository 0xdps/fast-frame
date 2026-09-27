# Admin deployment

Admin is mounted at all only when `"fastframe.admin"` is in
`INSTALLED_APPS` (see [admin-setup.md](admin-setup.md),
[app-contract.md](app-contract.md)). Once installed, three UI-mode
choices are selected in settings via `ADMIN_MODE`. The REST API
(`ADMIN_API_PREFIX`, default `/api/admin`) is the same in every mode.

`get_asgi_application()`/`create_app()` applies the choice for any
installed admin. You can also mount the pieces yourself with
`include_admin(app)` or the individual routers, without going through
`INSTALLED_APPS` at all (see `examples/blog_app`).

## Static admin (default)

`ADMIN_MODE = "static"` serves the compiled HTML, CSS, and JavaScript that
ship in `fastframe/admin/static`. No Node.js install is required.

```python
import os
os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.http.asgi import get_asgi_application

app = get_asgi_application()
```

Open `/admin/`. Resource URLs use a hash (`/admin/#/user`) because React Admin's default router is a hash router, which works when the UI is mounted under `ADMIN_PREFIX`. Working copy: `examples/admin_simple/`.

Framework checkouts refresh that bundle with:

```text
python manage.py buildadmin
```

`--source` and `--output` retarget the React project and the destination
directory. `--base` and `--api-url` set `VITE_BASE` and `VITE_API_URL`.

## Custom admin

`ADMIN_MODE = "custom"` serves `admin-ui/dist` from the project directory.

```text
python manage.py startadmin
cd admin-ui
npm install
npm run dev     # separate dev server on port 5173
npm run build   # dist mounted at /admin/ by the API process
```

Until `dist/index.html` exists, `/admin/` shows those commands instead of a
blank 404. The API still responds. Working copy: `examples/admin_custom/`.

Production builds default to Vite `base: "/admin/"`, matching `ADMIN_PREFIX`.
Dev (`npm run dev`) stays at `/` and calls `http://127.0.0.1:8000/api/admin`.

## No admin

Leave `"fastframe.admin"` out of `INSTALLED_APPS` (the default for a
freshly generated project). Nothing about the admin is imported or
mounted, and its routes are absent from OpenAPI. Set
`ENABLE_ADMIN_DOCS = False` when the admin stays *installed* but should
not appear in Swagger.

## OpenAPI

Leave `"fastframe.docs"` out of `INSTALLED_APPS` and `/docs`, `/redoc`,
and `/openapi.json` are not mounted. Add it when you want FastAPI's
Swagger. See [settings.md](settings.md).
