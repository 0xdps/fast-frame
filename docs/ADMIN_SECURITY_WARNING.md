# ⚠️ Admin Security Notes

**Current as of FastFrame v0.3.0**

---

## ✅ Session Authentication Is Built In

The admin API and UI require a logged-in `User` with `can_access_admin =
True` by default.

### How it works

- `POST /api/admin/login` — verify `{"username", "password"}`, set a signed,
  `httponly` session cookie (`ff_admin_session`, HMAC-SHA256 over
  `SECRET_KEY`, 14-day expiry).
- `POST /api/admin/logout` — clear the session cookie.
- `GET /api/admin/me` — return the current admin user, or `401` if not
  logged in.
- Every other `/api/admin/*` route requires that cookie and rejects requests
  with `401` (not logged in) or `403` (logged in, but `can_access_admin` is
  `False`).
- The bundled admin UI (`ADMIN_MODE = "static"`, the default, or `"custom"`
  for a project-built React app) serves a minimal login page instead of the
  SPA shell until a valid session exists.

### Granting admin access to a user

```python
from fastframe.contrib.auth.models import User
from fastframe.db.session import session_scope

with session_scope():
    user = User(username="admin", email="admin@example.com", password="")
    user.set_password("choose-a-strong-password")
    user.can_access_admin = True  # required to log into /admin
    user.save()
```

### Opting out (development only)

```python
# settings.py
ADMIN_REQUIRE_AUTH = False  # ⚠️ disables the login requirement entirely
```

Only do this on `localhost`/trusted networks — with it off, the admin has
**no authentication at all**. See "Current Security Gaps" below for what's
still not covered even with auth enabled.

---

## Current Security Gaps

Authentication is now handled. These are still open:

| Feature | Status | Risk |
|---------|--------|------|
| **Authentication** | ✅ Implemented (v0.3.0) | — |
| **Authorization (role/permission)** | ⚠️ Coarse only (`can_access_admin`, `is_superuser`) | MEDIUM |
| **Per-model/field permissions** | ❌ Not implemented (`has_*_permission` are static class attrs, not per-request) | MEDIUM |
| **CSRF Protection** | ❌ Not implemented (mitigated: cookie is `SameSite=Lax`) | MEDIUM |
| **Rate Limiting on `/login`** | ❌ Not implemented (brute-force is possible) | MEDIUM |
| **Audit Logging** | ❌ Not implemented | LOW |

---

## Deployment Checklist

Before deploying with admin enabled, ensure:

- [ ] `SECRET_KEY` is a long, random, unique value (never the dev default) —
      the session cookie's signature depends entirely on it.
- [ ] `DEBUG = False` in production, so session cookies are sent `Secure`
      (HTTPS-only).
- [ ] Only trusted users have `can_access_admin = True`.
- [ ] `ADMIN_REQUIRE_AUTH` is **not** set to `False` in production.
- [ ] Consider fronting `/admin` and `/api/admin` with a firewall/VPN as
      defense-in-depth, since fine-grained permissions aren't implemented yet.

---

## FAQ

### Q: Can I still add my own auth logic on top of this?
**A:** Yes. `require_admin_user` (in `fastframe.admin.auth`) is a normal
FastAPI dependency — replace or extend it, or add further dependencies to
the router returned by `get_admin_api_router()`.

### Q: What if a user's session cookie leaks?
**A:** Treat it like any session token — it grants admin access for up to 14
days or until logout. Rotate `SECRET_KEY` to invalidate all sessions
immediately (this also logs out every admin user).

### Q: Is the React Admin UI secure?
**A:** The bundled UI now gates behind login (see "How it works" above), but
it has no permission-aware widgets yet — any user who can log in and has
`can_access_admin` sees the same UI regardless of role.

### Q: What about fine-grained permissions (per-model, per-field)?
**A:** Not yet — `ModelAdmin.has_add_permission` etc. are still static
booleans, not per-request checks. Planned for v0.4 (see roadmap).

---

## Security Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| **v0.3.0** | Admin CRUD + session authentication (login/logout/me) | ✅ Released |
| **v0.4** | Fine-grained, per-request permissions | 📋 Planned |
| **v0.4** | CSRF protection | 📋 Planned |
| **v0.4** | Rate limiting on `/login` | 📋 Planned |
| **v0.4** | Audit logging | 📋 Planned |

See [docs/roadmap.md](roadmap.md#v04--harden-auth--authorization) for the
full v0.4 plan.

---

## Responsible Disclosure

If you discover a security issue in FastFrame:

1. **DO NOT** open a public GitHub issue
2. Email: [security@fastframe.dev](mailto:security@fastframe.dev) *(placeholder)*
3. Include: version, description, reproduction steps
4. We'll respond within 48 hours

---

## Learn More

- [Admin Setup Guide](admin-setup.md)
- [Roadmap](roadmap.md#v04--harden-auth--authorization)
- [Contributing Security Features](../CONTRIBUTING.md)

---

**FastFrame v0.3.0 admin requires login by default. Fine-grained permissions
are still on the roadmap — see the Security Roadmap above.**

*Updated: 2026-09-26*
