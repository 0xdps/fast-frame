"""Optional Celery integration.

Listing ``"fastframe.tasks"`` in ``INSTALLED_APPS`` is what turns it on.
Tasks are Celery's ``@shared_task``. See docs/tasks.md.
"""

from __future__ import annotations

from typing import Any


def __getattr__(name: str) -> Any:
    if name == "get_app":
        from fastframe.tasks.celery import get_app

        return get_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
