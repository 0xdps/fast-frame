"""Start the Celery worker or Beat from ``manage.py``."""

from __future__ import annotations

from fastframe.core.bootstrap import bootstrap


def load_app():
    """Bootstrap FastFrame and return the configured Celery app.

    Raises ``SystemExit`` when the tasks app is not installed or Celery
    itself is not installed.
    """
    try:
        registry = bootstrap(None)
    except ImportError as exc:
        raise SystemExit(f"Error: {exc}") from exc
    if not registry.is_installed("fastframe.tasks"):
        raise SystemExit('Error: add "fastframe.tasks" to INSTALLED_APPS to run background jobs.')
    from fastframe.tasks.celery import get_app

    return get_app()


def start(command: str, loglevel: str) -> None:
    """Run ``celery worker`` or ``celery beat`` and exit with its status."""
    app = load_app()
    code = app.start(argv=[command, "--loglevel", loglevel])
    if code:
        raise SystemExit(code)
