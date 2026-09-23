# Custom user model

`AUTH_USER_MODEL = "accounts.CustomUser"` replaces the built-in `auth.User`.
`get_user_model()` and `createadminuser` follow that setting.

```bash
python manage.py createadminuser --username admin --email admin@example.com --password admin123 --no-input
python -m uvicorn app:app --reload
```

The admin user list includes the extra `phone` field. Set `user_data["admin_access"]`
on accounts that should reach the admin UI once login checks are added; the
built-in model exposes that as `can_access_admin`.
