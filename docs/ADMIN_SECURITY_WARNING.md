# ⚠️ Admin Security Notes

**Current as of FastFrame v0.1.0**

---

## ✅ Session Authentication Is Built In

The admin API and UI require a logged-in `User` with `can_access_admin =
True` by default.

### How it works

- `POST /api/admin/login` — verify `{"username", "password"}` (rate-limited,
  see "Rate Limiting" below), set a signed, `httponly` session cookie
  (`ff_admin_session`, HMAC-SHA256 over `SECRET_KEY`, 14-day expiry). The
  cookie payload includes a `session_version` checked against the user's
  live value on every request — see "Session Revocation" below.
- `POST /api/admin/logout` — clear the session cookie.
- `GET /api/admin/me` — return the current admin user, or `401` if not
  logged in.
- Every other `/api/admin/*` route requires that cookie and rejects requests
  with `401` (not logged in) or `403` (logged in, but `can_access_admin` is
  `False`).
- The bundled admin UI (`ADMIN_MODE = "static"`, the default, or `"custom"`
  for a project-built React app) serves a minimal login page instead of the
  SPA shell until a valid session exists.
- The same session cookie now also works for general, non-admin app
  routes via `POST /api/auth/login` / `/logout` / `GET /api/auth/me` — see
  [auth.md](auth.md#general-purpose-session-auth-outside-admin).

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

Authentication and authorization are now handled. These are still open:

| Feature | Status | Risk |
|---------|--------|------|
| **Authentication** | ✅ Implemented | — |
| **Authorization (role/permission)** | ✅ Implemented — opt-in, per-model/per-request via `Group`/permission strings; see [permissions.md](permissions.md) | — |
| **Per-model/field permissions** | ✅ Implemented — `enforce_permissions`, `readonly_fields`/`fields`/`exclude` now actually enforced on write, not just rendering | — |
| **Session revocation** | ✅ Implemented — `user.invalidate_sessions()` server-side "log out everywhere" | — |
| **Timing-safe login** | ✅ Implemented — constant-time hash compare, dummy-hash on unknown/inactive username | — |
| **Rate Limiting on `/login` / `/api/auth/token`** | ✅ Implemented — in-memory sliding window + lockout; see "Rate Limiting" below | — |
| **CORS / security headers** | ✅ Implemented — opt-in `CORS_ALLOWED_ORIGINS`, `SECURE_HEADERS` on by default | — |
| **CSRF Protection** | ⚠️ Mitigated only (cookie is `SameSite=Lax`; no CSRF token) | LOW-MEDIUM |
| **Per-object (row-level) permissions** | ❌ Not implemented — permissions are per-model only | LOW |
| **`ManyToManyField(through=...)`** | ❌ Not implemented — deferred, see the [roadmap](https://github.com/0xdps/fast-frame/blob/trunk/docs/roadmap.md) | — |
| **Audit Logging** | ✅ Implemented — see below | — |

---

## Rate Limiting

`/api/admin/login`, `/api/auth/login`, and `/api/auth/token` are all
rate-limited: after `RATE_LIMIT_LOGIN_MAX_ATTEMPTS` failed attempts within
`RATE_LIMIT_LOGIN_WINDOW_SECONDS`, the identifier (username + client IP)
is locked out for `RATE_LIMIT_LOGIN_LOCKOUT_SECONDS` and gets `429` with a
`Retry-After` header. A successful login resets the counter.

This is an **in-memory, single-process** limiter
(`fastframe.core.ratelimit`) — it does not coordinate across multiple app
instances/workers behind a load balancer. It blunts naive, single-process
brute-forcing; it is not a substitute for a shared backend (Redis, etc.)
in a genuinely multi-instance deployment. See
[settings.md](settings.md#rate-limiting).

## Session Revocation

Session cookies carry a `session_version` alongside the user id. Calling
`user.invalidate_sessions()` (then `user.save()`) bumps that counter,
which immediately invalidates every previously issued cookie for that
user — the next request with an old cookie gets `401`, without needing a
server-side session table. Useful after a password change, or to force
sign-out on a suspected compromised session.

## Timing-Safe Authentication

`check_password()` compares hashes with `hmac.compare_digest` instead of
`==`. `authenticate()` always performs a full password-hash comparison —
against a dummy hash — even when the username doesn't exist or the
account is inactive, so a failed login for an unknown username takes
approximately the same time as a failed login for a real one. This closes
a username-enumeration-via-timing side channel that would otherwise
exist.

## Password Policy

`User.set_password()` now validates strength before hashing:
`PASSWORD_MIN_LENGTH` (default `8`), and rejects a password equal to the
username (case-insensitively). Pass `validate=False` to bypass this (e.g.
for scripted test fixtures).

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
  `AuditLog` is registered like any other model, installing `fastframe.api`
  (the generic REST API) lets any active user read the full audit log
  (`GET /api/v1/auditlog`), including other users' actions. Tighten
  `AuditLogAdmin.has_view_permission` if that's not acceptable for your
  project. `GET /api/v1/counts` (and `/api/admin/counts`) applies the same
  `has_view_permission` check per model before including its row count, so
  it does not add a *new* exposure here — but it's still one call that
  surfaces row totals (including `AuditLog`'s) for every model the caller
  can view, rather than one resource at a time.

---

## Deployment Checklist

Before deploying with admin enabled, ensure:

- [ ] `SECRET_KEY` is a long, random, unique value (never the dev default) —
      the session cookie's signature depends entirely on it.
- [ ] `DEBUG = False` in production, so session cookies are sent `Secure`
      (HTTPS-only).
- [ ] Only trusted users have `can_access_admin = True`.
- [ ] Consider fronting `/admin` and `/api/admin` with a firewall/VPN as
      defense-in-depth — per-model permissions exist (opt-in via
      `enforce_permissions`, see [permissions.md](permissions.md)) but
      there's still no per-object (row-level) enforcement.
- [ ] If `fastframe.api` (the generic REST API) is in `INSTALLED_APPS`,
      remember it's reachable by **any active user** (not just admins) and
      shares the admin registry — review `has_view_permission`/
      `enforce_permissions` on sensitive models (including `AuditLog`)
      before installing it. See [rest-api.md](rest-api.md).
- [ ] If serving browser clients from a different origin, set
      `CORS_ALLOWED_ORIGINS` explicitly rather than leaving it disabled —
      and never combine `CORS_ALLOW_CREDENTIALS = True` with a wildcard
      origin.
- [ ] Leave `SECURE_HEADERS = True` (the default) in production so
      `Strict-Transport-Security` is sent (it's only added when
      `DEBUG = False`).

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
**A:** Opt in per model with `enforce_permissions = True` to
turn `has_*_permission` into per-request checks against Django-style
permission strings (`Group`, `User.permissions`). `readonly_fields`,
`fields`, and `exclude` are now actually enforced on write, not just used
for UI rendering. Per-*object* (row-level) permissions are still not
implemented. See [permissions.md](permissions.md).

---

## Security Roadmap

Everything below marked "Released" shipped together in **v0.1.0**, the
first tagged release — see [CHANGELOG.md](https://github.com/0xdps/fast-frame/blob/trunk/CHANGELOG.md).

| Feature | Status |
|---------|--------|
| Admin CRUD + session authentication (login/logout/me) | ✅ Released |
| Audit logging (admin + REST API) | ✅ Released |
| Generic token-authenticated REST API | ✅ Released |
| Fine-grained, per-request permissions (`Group`, permission strings) | ✅ Released |
| `readonly_fields`/`fields`/`exclude` enforced on write | ✅ Released |
| General-purpose session auth outside `/admin` | ✅ Released |
| Server-side session revocation | ✅ Released |
| Rate limiting on login/token endpoints | ✅ Released |
| CORS + security headers + `MIDDLEWARE` setting | ✅ Released |
| Timing-safe authentication, password strength policy, token expiry | ✅ Released |
| CSRF token (beyond `SameSite=Lax` mitigation) | 📋 Planned |
| Per-object (row-level) permissions | 📋 Planned |
| `ManyToManyField(through=...)` | 📋 Planned |

See the [roadmap](https://github.com/0xdps/fast-frame/blob/trunk/docs/roadmap.md) for the full plan.

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
- [Permissions](permissions.md)
- [Auth](auth.md)
- [REST API](rest-api.md)
- [Settings](settings.md)
- [Roadmap](https://github.com/0xdps/fast-frame/blob/trunk/docs/roadmap.md)
- [Contributing Security Features](https://github.com/0xdps/fast-frame/blob/trunk/CONTRIBUTING.md)

---

**FastFrame v0.1.0 admin requires login by default and supports opt-in,
per-request permissions, rate limiting, session revocation, and
CORS/security headers. CSRF tokens and per-object permissions are still on
the roadmap — see the Security Roadmap above.**

*Updated: 2026-09-26*
