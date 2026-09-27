"""Built-in, opt-in health-check app.

Listing ``"fastframe.health"`` in ``INSTALLED_APPS`` mounts a ``GET
/health`` endpoint (path configurable via ``HEALTH_PATH``). A project can
override the check itself — its function *and* its response — by pointing
``HEALTH_CHECK`` at its own callable. Leave it out and the endpoint simply
isn't mounted, the same way ``fastframe.admin`` / ``fastframe.docs`` are
opt-in.

See docs/settings.md.
"""

from fastframe.health.apps import HealthConfig
from fastframe.health.views import get_health_router

__all__ = ["HealthConfig", "get_health_router"]