# FastFrame Admin UI

React Admin frontend for the FastFrame admin REST API. Resources, list columns, and forms are generated from `GET /api/admin/schema`.

## Run

Start the API first (from `examples/blog_app`):

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Then start the UI:

```bash
cd admin-ui
npm install
npm run dev
```

Open http://localhost:5173

Optional: `VITE_API_URL` overrides the API base (default `http://127.0.0.1:8000/api/admin`).
