# Admin deployment

Three choices, selected in settings. The REST API (`ADMIN_API_PREFIX`,
default `/api/admin`) is the same in every mode. `ENABLE_ADMIN = False`
mounts neither the UI nor the API.

`create_app()` applies the choice. You can also mount the pieces yourself
with `include_admin(app)` or the individual routers.

## Static admin (default)

`ADMIN_MODE = "static"` serves the compiled HTML, CSS, and JavaScript that
ship in `fastframe/admin/static`. No Node.js install is required.

```python
import os
os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.core.app import create_app

app = create_app()
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

```python
ENABLE_ADMIN = False
```

`create_app()` leaves admin routes out of the app and out of OpenAPI.
Set `ENABLE_ADMIN_DOCS = False` when the admin stays mounted but should not
appear in Swagger.

## OpenAPI

```python
ENABLE_OPENAPI = False          # no /docs, /redoc, or /openapi.json
SWAGGER_UI_URL = None           # hide Swagger only
REDOC_URL = None                # hide ReDoc only
```

See [settings.md](settings.md).
