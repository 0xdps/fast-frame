# Simple admin

The compiled admin that ships with FastFrame. No Node.js required.

```bash
python manage.py createadminuser --username admin --email admin@example.com --password admin123 --no-input
python -m uvicorn app:app --reload
```

- UI: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/admin/schema
- Swagger: http://127.0.0.1:8000/docs

`get_asgi_application()`/`create_app()` reads `ADMIN_MODE = "static"` and the OpenAPI
settings, and mounts admin because `"fastframe.admin"` is in `INSTALLED_APPS`. Turn
admin off by removing it from `INSTALLED_APPS`. Hide Swagger with
`ENABLE_OPENAPI = False` or `SWAGGER_UI_URL = None`.
