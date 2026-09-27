# Simple admin

The compiled admin that ships with FastFrame. No Node.js required.

```bash
python manage.py createadminuser --username admin --email admin@example.com --password admin123 --no-input
python -m uvicorn app:app --reload
```

- UI: http://127.0.0.1:8000/admin/
- API: http://127.0.0.1:8000/api/admin/schema
- Swagger: http://127.0.0.1:8000/docs

`get_asgi_application()`/`create_app()` reads `ADMIN_MODE = "static"` and mounts
admin because `"fastframe.admin"` is in `INSTALLED_APPS`. Swagger is mounted
because `"fastframe.docs"` is listed too. Remove either app to turn that
piece off.
