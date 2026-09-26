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

### There is no opt-out

Unlike earlier drafts of this doc, `ADMIN_REQUIRE_AUTH` does not exist —
authentication cannot be disabled, even for local development. Every
`/api/admin/*` route (and the admin UI shell) always requires a valid
session. See "Current Security Gaps" below for what's still not covered
even with auth enabled.

---

## Current Security Gaps

Authentication is now handled. These are still open:

| Feature | Status | Risk |
|---------|--------|------|
| **Authentication** | ✅ Implemented (v0.3.0) | — |
| **Authorization (role/permission)** | ⚠️ Coarse only (`can_access_admin`, `is_superuser`) | MEDIUM |
| **Per-model/field permissions** | ❌ Not implemented (`has_*_permission` are static class attrs, not per-request) | MEDIUM |
| **CSRF Protection** | ❌ Not implemented (mitigated: cookie is `SameSite=Lax`) | MEDIUM |
| **Rate Limiting on `/login` / `/api/auth/token`** | ❌ Not implemented (brute-force is possible) | MEDIUM |
| **Audit Logging** | ✅ Implemented (v0.3.0) — see below | — |

---

## Audit Logging

Every create, update, and delete made through the admin API or the [REST
API](rest-api.md) is recorded in `AuditLog` (`fastframe.admin.audit`):
who (`user_id`, `username`), what (`action`, `model_name`, `object_id`,
`object_repr`), when (`created_at`), which surface (`source`: `"admin"` or
`"api"`), and the values that changed (`changes` — full snapshot for
create/delete, `{field: {"old", "new"}}` diff of only changed fields for
update).

- Read-only: registered with `admin_site` so it's browsable in the admin
  UI, but `has_add_permission` / `has_change_permission` /
  `has_delete_permission` are all `False` — it can't be edited or deleted
  through either API.
- Best-effort: a failure writing an audit entry never blocks or fails the
  action it's recording (`record_audit()` swallows its own exceptions).
- Login/logout and failed-login attempts are **not** recorded — only
  mutating CRUD actions.
- **Visible to any active token-holding user, not just admins**: because
  `AuditLog` is registered like any other model, enabling `ENABLE_REST_API`
  lets any active user read the full audit log (`GET /api/v1/auditlog`),
  including other users' actions. Tighten `AuditLogAdmin.has_view_permission`
  if that's not acceptable for your project.

---

## Deployment Checklist

Before deploying with admin enabled, ensure:

- [ ] `SECRET_KEY` is a long, random, unique value (never the dev default) —
      the session cookie's signature depends entirely on it.
- [ ] `DEBUG = False` in production, so session cookies are sent `Secure`
      (HTTPS-only).
- [ ] Only trusted users have `can_access_admin = True`.
- [ ] Consider fronting `/admin` and `/api/admin` with a firewall/VPN as
      defense-in-depth, since fine-grained permissions aren't implemented yet.
- [ ] If `ENABLE_REST_API = True`, remember it's reachable by **any active
      user** (not just admins) and shares the admin registry — review
      `has_view_permission` on sensitive models (including `AuditLog`)
      before enabling it. See [rest-api.md](rest-api.md).

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
| **v0.4** | Rate limiting on `/login` and `/api/auth/token` | 📋 Planned |
| **v0.3.0** | Audit logging (admin + REST API) | ✅ Released |
| **v0.3.0** | Generic token-authenticated REST API | ✅ Released |

See [docs/roadmap.md](roadmap.md) for the full v0.4 plan.

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
- [REST API](rest-api.md)
- [Roadmap](roadmap.md)
- [Contributing Security Features](../CONTRIBUTING.md)

---

**FastFrame v0.3.0 admin requires login by default. Fine-grained permissions
are still on the roadmap — see the Security Roadmap above.**

*Updated: 2026-09-26*
