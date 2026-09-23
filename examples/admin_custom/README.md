# Custom admin

`ADMIN_MODE = "custom"` serves `admin-ui/dist` from this project. The React
source is yours to change (theme, layout, extra pages).

```bash
python manage.py startadmin
cd admin-ui
npm install
npm run dev          # http://localhost:5173 while the API runs on :8000
npm run build        # writes admin-ui/dist, served at /admin/
```

`npm run build` uses Vite base `/admin/` so asset URLs match the FastAPI mount.
For a separately hosted UI, build with `VITE_BASE=/` and `VITE_API_URL` pointing
at the API.

Rebuild the copy that ships inside FastFrame itself with:

```bash
python manage.py buildadmin
```
