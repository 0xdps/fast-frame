# ⚠️ Admin Security Warning

**FastFrame v0.3.0 - Admin Preview Release**

---

## 🔴 CRITICAL: Admin is Development-Only in v0.3.0

The FastFrame admin system in v0.3.0 **does not include authentication or authorization**. 

### What This Means

✅ **Safe for development:**
- Running on `localhost`
- Behind VPN or firewall
- Internal networks only

❌ **NOT SAFE for production:**
- Public internet access
- Shared hosting
- Cloud deployments without security groups
- Any untrusted network

---

## Current Security Gaps

| Feature | Status | Risk |
|---------|--------|------|
| **Authentication** | ❌ Not implemented | CRITICAL |
| **Authorization** | ❌ Not implemented | CRITICAL |
| **CSRF Protection** | ❌ Not implemented | HIGH |
| **Rate Limiting** | ❌ Not implemented | MEDIUM |
| **Audit Logging** | ❌ Not implemented | LOW |

---

## Immediate Actions

### If You're Using v0.3.0 Admin:

**Option 1: Development Only (Recommended)**
```python
# settings.py
import os

# Only enable admin in development
DEBUG = os.getenv("DEBUG", "False") == "True"
ENABLE_ADMIN = DEBUG  # Admin only when DEBUG=True

# In production
# DEBUG=False ENABLE_ADMIN=False
```

**Option 2: Firewall Protection**
- Use firewall rules to block `/admin` and `/api/admin` from public access
- Only allow access from VPN IPs
- Use AWS Security Groups, GCP Firewall Rules, etc.

**Option 3: Disable Admin Entirely**
```python
# settings.py
ENABLE_ADMIN = False
```

**Option 4: Wait for v0.3.1**
- v0.3.1 will add authentication
- Planned release: 2-3 weeks after v0.3.0

---

## What's Coming in v0.3.1

### Authentication System
- ✅ Session-based authentication
- ✅ Login/logout endpoints
- ✅ User.can_access_admin checks
- ✅ Permission validation on all admin endpoints
- ✅ Automatic redirect to login page

### Authorization
- ✅ Model-level permissions (view, add, change, delete)
- ✅ Field-level permissions
- ✅ Custom permission checks via `has_permission()`
- ✅ Integration with `User.permissions` JSON field

---

## FAQ

### Q: Can I add authentication myself in v0.3.0?
**A:** Yes! You can add FastAPI dependencies to admin routes:

```python
from fastapi import Depends, HTTPException
from fastframe.admin import get_admin_api_router

async def require_admin(request: Request):
    # Your auth logic here
    user = await get_current_user(request)
    if not user or not user.can_access_admin:
        raise HTTPException(403, "Admin access required")
    return user

# Add dependency to admin router
router = get_admin_api_router()
router.dependencies.append(Depends(require_admin))
```

### Q: What if someone accesses my dev admin?
**A:** They can:
- View all model data
- Create/edit/delete any records
- Access user information

### Q: Is the React Admin UI secure?
**A:** The UI itself is fine, but it makes API calls without authentication. Anyone who can access the UI can use the API.

### Q: Should I use admin in production at all?
**A:** **Not in v0.3.0**. Wait for v0.3.1 with authentication, or implement your own auth layer.

### Q: What about read-only access?
**A:** Even read-only access exposes data. All endpoints (GET, POST, PUT, DELETE) are unprotected in v0.3.0.

---

## Deployment Checklist

Before deploying with admin enabled, ensure:

- [ ] `ENABLE_ADMIN=False` in production, OR
- [ ] Admin only accessible via VPN/internal network, OR
- [ ] Firewall blocks `/admin` and `/api/admin` from public, OR
- [ ] Custom authentication added as shown above

**Default is `ENABLE_ADMIN=True`** - you must explicitly disable or secure it!

---

## Security Roadmap

| Version | Feature | Status |
|---------|---------|--------|
| **v0.3.0** | Admin CRUD (no auth) | ✅ Released |
| **v0.3.1** | Authentication | 🚧 In progress |
| **v0.3.2** | Fine-grained permissions | 📋 Planned |
| **v0.4.0** | CSRF protection | 📋 Planned |
| **v0.4.0** | Rate limiting | 📋 Planned |
| **v0.5.0** | Audit logging | 📋 Planned |

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

**Remember: FastFrame v0.3.0 admin is a preview release for development use only.**

*Updated: 2026-09-23*
