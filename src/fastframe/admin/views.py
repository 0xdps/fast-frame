"""Admin UI router — serves the React admin app (or a "build it" page).

The admin UI is React-only (Tailwind, built with Vite). There is no
server-rendered fallback: ``ADMIN_MODE`` only selects *which* React build to
serve — the pre-built one shipped with FastFrame (``"static"``, the default)
or a project-customized one (``"custom"``, via ``manage.py startadmin``).
Both talk to the same JSON REST API in ``fastframe.admin.api``.
"""

from __future__ import annotations

import json

# Templates directory
import pathlib
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

ADMIN_DIR = pathlib.Path(__file__).parent


def _admin_settings() -> tuple[str, str]:
    """Return (mode, url prefix) from settings, with safe defaults."""
    try:
        from fastframe.conf import settings

        return (
            str(getattr(settings, "ADMIN_MODE", "static")),
            str(getattr(settings, "ADMIN_PREFIX", "/admin")),
        )
    except (ImportError, AttributeError):
        return "static", "/admin"


def _admin_api_prefix() -> str:
    """Return ADMIN_API_PREFIX from settings, with a safe default."""
    try:
        from fastframe.conf import settings

        return str(getattr(settings, "ADMIN_API_PREFIX", "/api/admin"))
    except (ImportError, AttributeError):
        return "/api/admin"


_LOGIN_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>FastFrame Admin — Sign in</title>
<style>
body{font-family:system-ui,sans-serif;max-width:22rem;margin:6rem auto;padding:0 1rem;color:#172033}
h1{font-size:1.25rem}
label{display:block;margin-top:.75rem;font-size:.875rem;color:#475569}
input{width:100%;padding:.5rem;margin-top:.25rem;border:1px solid #cbd5e1;
border-radius:6px;box-sizing:border-box}
button{margin-top:1.25rem;width:100%;padding:.6rem;border:0;border-radius:6px;
background:#2563eb;color:#fff;font-weight:600;cursor:pointer}
button:disabled{opacity:.6;cursor:default}
#error{color:#dc2626;font-size:.875rem;margin-top:.75rem;display:none}
</style></head>
<body>
<h1>FastFrame Admin</h1>
<form id="login-form">
  <label>Username
    <input type="text" name="username" autocomplete="username" required>
  </label>
  <label>Password
    <input type="password" name="password" autocomplete="current-password" required>
  </label>
  <div id="error"></div>
  <button type="submit">Sign in</button>
</form>
<script>
const API_LOGIN_URL = __API_LOGIN_URL__;
const form = document.getElementById('login-form');
const errorEl = document.getElementById('error');
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  errorEl.style.display = 'none';
  const btn = form.querySelector('button');
  btn.disabled = true;
  try {
    const res = await fetch(API_LOGIN_URL, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      credentials: 'include',
      body: JSON.stringify({
        username: form.username.value,
        password: form.password.value,
      }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      errorEl.textContent = (body.detail && body.detail.message)
        || body.detail || 'Invalid username or password';
      errorEl.style.display = 'block';
      btn.disabled = false;
      return;
    }
    window.location.reload();
  } catch (err) {
    errorEl.textContent = 'Network error \u2014 please try again';
    errorEl.style.display = 'block';
    btn.disabled = false;
  }
});
</script>
</body></html>"""


def _login_page_html(api_prefix: str) -> str:
    """Render a minimal, dependency-free login page for the admin UI.

    Posts credentials to ``{api_prefix}/login`` and reloads on success so the
    server can serve the real admin content once the session cookie is set.
    """
    login_url = json.dumps(f"{api_prefix}/login")
    return _LOGIN_PAGE_TEMPLATE.replace("__API_LOGIN_URL__", login_url)


def _admin_login_redirect(request: Request) -> HTMLResponse | None:
    """Return a login page response if the request isn't authenticated.

    Returns None when the request already carries a valid admin session,
    meaning the real view should proceed. Admin auth is always required —
    there is no setting to disable it.
    """
    from fastframe.admin.auth import get_current_admin_user

    if get_current_admin_user(request) is not None:
        return None
    return HTMLResponse(_login_page_html(_admin_api_prefix()))


def _built_admin_router(directory: pathlib.Path, prefix: str) -> APIRouter:
    """Serve a built React SPA (index.html + hashed assets) under ``prefix``.

    Unauthenticated requests get a minimal login page instead of the SPA
    shell, since the SPA itself has no built-in login flow (see
    ``docs/ADMIN_SECURITY_WARNING.md``). Once the session cookie is set via
    ``/api/admin/login``, a page reload serves the real assets.
    """
    from fastapi.responses import FileResponse

    root = directory.resolve()
    router = APIRouter(prefix=prefix, tags=["admin"], include_in_schema=False)

    def _file_for(full_path: str) -> pathlib.Path:
        if not full_path or full_path.endswith("/"):
            return root / "index.html"
        candidate = (root / full_path).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            return root / "index.html"
        if candidate.is_file():
            return candidate
        return root / "index.html"

    @router.get("")
    @router.get("/")
    @router.get("/{full_path:path}")
    async def serve_built_admin(request: Request, full_path: str = "") -> Any:
        login_page = _admin_login_redirect(request)
        if login_page is not None:
            return login_page
        return FileResponse(_file_for(full_path))

    return router


def _custom_admin_missing_router(prefix: str) -> APIRouter:
    """Explain how to build the advanced admin when dist/ is not present."""
    router = APIRouter(prefix=prefix, tags=["admin"], include_in_schema=False)
    page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>FastFrame Admin</title>
<style>
body{font-family:system-ui,sans-serif;max-width:40rem;margin:4rem auto;padding:0 1rem;color:#172033}
code,pre{background:#f4f7fb;border-radius:8px}
pre{padding:1rem;overflow:auto}
</style></head>
<body>
<h1>Admin UI is not built yet</h1>
<p>This project uses the advanced admin (<code>ADMIN_MODE = "custom"</code>).
Generate it, then build the static files:</p>
<pre>python manage.py startadmin
cd admin-ui
npm install
npm run build</pre>
<p>Restart the server and open this page again. The REST API stays available
at the admin API prefix either way.</p>
</body></html>"""

    @router.get("")
    @router.get("/")
    @router.get("/{full_path:path}")
    async def missing_custom_admin(full_path: str = "") -> HTMLResponse:
        del full_path
        return HTMLResponse(page)

    return router


def get_admin_router() -> APIRouter:
    """Create and return the admin UI router.

    ``ADMIN_MODE`` selects which React build is served:

    * ``static`` (default) — the compiled admin shipped with FastFrame
    * ``custom`` — ``admin-ui/dist`` produced by ``startadmin`` + ``npm run build``

    Any other/unrecognized value falls back to ``static``. Whether this
    is reachable at all is controlled by whether ``"fastframe.admin"`` is
    in ``INSTALLED_APPS`` (see :class:`fastframe.admin.apps.AdminConfig`),
    not a setting here.
    """
    admin_mode, prefix = _admin_settings()

    if admin_mode == "custom":
        dist = pathlib.Path.cwd() / "admin-ui" / "dist"
        if (dist / "index.html").is_file():
            return _built_admin_router(dist, prefix)
        return _custom_admin_missing_router(prefix)

    return _built_admin_router(ADMIN_DIR / "static", prefix)


__all__ = ["get_admin_router"]
