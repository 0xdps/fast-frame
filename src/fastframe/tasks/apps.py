"""AppConfig for background jobs.

Listing ``"fastframe.tasks"`` in ``INSTALLED_APPS`` is what configures
Celery. A new project does not include it. See docs/tasks.md.
"""

from __future__ import annotations

from fastframe.core.apps import AppConfig


class TasksConfig(AppConfig):
    name = "fastframe.tasks"
    label = "tasks"

    def ready(self) -> None:
        try:
            from fastframe.tasks.celery import configure_from_settings
        except ImportError as exc:
            raise ImportError(
                'fastframe.tasks requires Celery. Install it with: pip install "fast-frame[tasks]"'
            ) from exc
        configure_from_settings()

    def checks(self):
        from fastframe.conf import settings
        from fastframe.core.checks import ERROR, CheckMessage

        if settings.CELERY_TASK_ALWAYS_EAGER:
            return []
        if str(settings.CELERY_BROKER_URL or "").strip():
            return []
        return [
            CheckMessage(
                level=ERROR,
                message="CELERY_BROKER_URL is empty.",
                hint="Set it to a Redis URL, for example redis://localhost:6379/0.",
                id="tasks.E001",
                obj="fastframe.tasks",
            )
        ]
