# ⚠️ Admin Security Notes

**FastFrame v0.3.1 - Admin Authentication**

---

## ✅ UPDATE (v0.3.1): Session Authentication Is Now Built In

As of v0.3.1, the admin API and UI require a logged-in `User` with
`can_access_admin = True` by default. This closes the critical gap flagged
in v0.3.0 (see "v0.3.0 History" below).

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
- The bundled admin UI (`ADMIN_MODE = "static"`, the default) serves a
  minimal login page instead of the SPA shell until a valid session exists;
  the SSR (`ADMIN_MODE = "ssr"`) views do the same.

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

Only do this on `localhost`/trusted networks — with it off, admin behaves
exactly like v0.3.0 (no authentication at all). See "Current Security Gaps"
below for what's still not covered even with auth enabled.

---

## Current Security Gaps

Authentication is now handled. These are still open:

| Feature | Status | Risk |
|---------|--------|------|
| **Authentication** | ✅ Implemented (v0.3.1) | — |
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
booleans, not per-request checks. Planned for v0.3.2 (see roadmap).

---

## Security Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| **v0.3.0** | Admin CRUD (no auth) | ✅ Released |
| **v0.3.1** | Session authentication (login/logout/me) | ✅ Released |
| **v0.3.2** | Fine-grained, per-request permissions | 📋 Planned |
| **v0.4.0** | CSRF protection | 📋 Planned |
| **v0.4.0** | Rate limiting | 📋 Planned |
| **v0.5.0** | Audit logging | 📋 Planned |

---

## v0.3.0 History (for context)

In v0.3.0, the admin system shipped with **no authentication or
authorization at all** — every `/api/admin/*` route was open to anyone who
could reach it. That gap is what v0.3.1's session authentication (above)
closes. If you're still running v0.3.0, upgrade or apply the workarounds
that were documented at the time (disable admin, or firewall it off).

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
- [Authentication Roadmap](roadmap.md#v04--authentication-and-authorization)
- [Contributing Security Features](../CONTRIBUTING.md)

---

**FastFrame v0.3.1 admin requires login by default. Fine-grained permissions
are still on the roadmap — see the Security Roadmap above.**

*Updated: 2026-09-26*
