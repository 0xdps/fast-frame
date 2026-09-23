# Simple admin

The compiled admin that ships with FastFrame. No Node.js required.

```bash
python manage.py createadminuser --username admin --email admin@example.com --password admin123 --no-input
python -m uvicorn app:app --reload
```

- UI: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/admin/schema
- Swagger: http://127.0.0.1:8000/docs

`create_app()` reads `ENABLE_ADMIN`, `ADMIN_MODE = "static"`, and the OpenAPI settings.
Turn admin off with `ENABLE_ADMIN = False`. Hide Swagger with `ENABLE_OPENAPI = False`
or `SWAGGER_UI_URL = None`.
