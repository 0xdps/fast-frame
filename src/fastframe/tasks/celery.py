"""The Celery application FastFrame configures from settings.

Importing this module requires the ``tasks`` extra
(``pip install "fast-frame[tasks]"``). ``AppConfig.ready()`` is the only
caller, and it runs only when ``"fastframe.tasks"`` is installed.
"""

from __future__ import annotations

from celery import Celery, Task

_app: Celery | None = None


class SessionTask(Task):  # pylint: disable=abstract-method
    """Run the task body in its own database session.

    The session is not the one bound to the current request. It commits
    when the task returns and rolls back when the task raises.
    """

    abstract = True

    def __call__(self, *args, **kwargs):
        from fastframe.db.session import session_scope

        with session_scope():
            return super().__call__(*args, **kwargs)


def get_app() -> Celery:
    """Return the process-wide Celery app, creating it on first use."""
    global _app
    if _app is None:
        _app = Celery("fastframe")
        _app.Task = SessionTask
        _app.set_default()
    return _app


def configure_from_settings() -> Celery:
    """Apply FastFrame settings and import each installed app's ``tasks.py``."""
    from fastframe.conf import settings
    from fastframe.core.bootstrap import get_apps_registry

    app = get_app()
    conf: dict = {
        "broker_url": settings.CELERY_BROKER_URL,
        "task_always_eager": bool(settings.CELERY_TASK_ALWAYS_EAGER),
        "task_eager_propagates": bool(settings.CELERY_TASK_ALWAYS_EAGER),
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "beat_schedule": dict(getattr(settings, "CELERY_BEAT_SCHEDULE", None) or {}),
    }
    backend = getattr(settings, "CELERY_RESULT_BACKEND", None)
    if backend:
        conf["result_backend"] = backend
    app.conf.update(conf)
    app.autodiscover_tasks([config.name for config in get_apps_registry().app_configs], force=True)
    return app
