"""Background jobs: Celery, eager execution, and the work/beat commands."""

from __future__ import annotations

import argparse
from contextlib import contextmanager

import pytest


@contextmanager
def _tasks_settings(*, eager: bool, broker: str = "redis://localhost:6379/0", schedule=None, install: bool = True):
    import config.settings as project_settings

    from fastframe.core.bootstrap import bootstrap, reset_bootstrap
    from fastframe.migrations.runner import migrate

    original_apps = list(project_settings.INSTALLED_APPS)
    original = {
        name: getattr(project_settings, name, None)
        for name in (
            "CELERY_TASK_ALWAYS_EAGER",
            "CELERY_BROKER_URL",
            "CELERY_BEAT_SCHEDULE",
            "CELERY_RESULT_BACKEND",
        )
    }
    apps = [app for app in original_apps if app != "fastframe.tasks"]
    if install:
        apps.append("fastframe.tasks")
    project_settings.INSTALLED_APPS = apps
    project_settings.CELERY_TASK_ALWAYS_EAGER = eager
    project_settings.CELERY_BROKER_URL = broker
    project_settings.CELERY_BEAT_SCHEDULE = {} if schedule is None else schedule
    project_settings.CELERY_RESULT_BACKEND = None
    reset_bootstrap()
    registry = bootstrap(None)
    if install:
        migrate()
    try:
        yield registry
    finally:
        project_settings.INSTALLED_APPS = original_apps
        for name, value in original.items():
            if value is None and not hasattr(project_settings, name):
                continue
            setattr(project_settings, name, value)
        reset_bootstrap()


def test_tasks_app_is_off_unless_installed(miniproject_env) -> None:
    from fastframe.core.bootstrap import get_apps_registry

    assert not get_apps_registry().is_installed("fastframe.tasks")


def test_eager_delay_runs_in_process(miniproject_env) -> None:
    with _tasks_settings(eager=True):
        from celery import shared_task

        @shared_task(name="tests.add")
        def add(left: int, right: int) -> int:
            return left + right

        result = add.delay(2, 3)
        assert result.get() == 5


def test_task_commits_on_its_own_session(miniproject_env) -> None:
    with _tasks_settings(eager=True):
        from celery import shared_task
        from users.models import User

        from fastframe.db.session import session_scope

        @shared_task(name="tests.create_user")
        def create_user(email: str) -> int:
            user = User(email=email, is_active=True)
            user.save()
            return user.id

        created_id = create_user.delay("ada@example.com").get()
        with session_scope():
            found = User.objects.get(email="ada@example.com")
            assert found.id == created_id


def test_beat_schedule_comes_from_settings(miniproject_env) -> None:
    with _tasks_settings(eager=True, schedule={"tick": {"task": "tests.tick", "schedule": 60.0}}):
        from fastframe.tasks.celery import get_app

        entry = get_app().conf.beat_schedule["tick"]
        assert entry["task"] == "tests.tick"
        assert entry["schedule"] == 60.0


def test_check_requires_a_broker_url(miniproject_env) -> None:
    from fastframe.core.bootstrap import get_apps_registry
    from fastframe.core.checks import ERROR, run_checks

    with _tasks_settings(eager=False, broker=""):
        messages = run_checks(get_apps_registry())
        assert any(message.id == "tasks.E001" and message.level == ERROR for message in messages)


def test_eager_mode_skips_the_broker_check(miniproject_env) -> None:
    from fastframe.core.bootstrap import get_apps_registry
    from fastframe.core.checks import run_checks

    with _tasks_settings(eager=True, broker=""):
        messages = run_checks(get_apps_registry())
        assert not any(message.id == "tasks.E001" for message in messages)


def test_work_refuses_to_start_when_tasks_are_not_installed(miniproject_env) -> None:
    from fastframe.cli.commands.work import execute

    with _tasks_settings(eager=True, install=False):
        with pytest.raises(SystemExit, match="INSTALLED_APPS"):
            execute(argparse.Namespace(loglevel="info"))


def test_work_and_beat_dispatch_celery(miniproject_env, monkeypatch) -> None:
    with _tasks_settings(eager=True):
        from fastframe.tasks.celery import get_app

        calls: list[list[str]] = []

        def fake_start(argv=None):
            calls.append(list(argv or []))
            return None

        monkeypatch.setattr(get_app(), "start", fake_start)

        from fastframe.cli.commands.beat import execute as run_beat
        from fastframe.cli.commands.work import execute as run_work

        run_work(argparse.Namespace(loglevel="info"))
        run_beat(argparse.Namespace(loglevel="warning"))
        assert calls[0][:2] == ["worker", "--loglevel"]
        assert calls[0][2] == "info"
        assert calls[1][:2] == ["beat", "--loglevel"]
        assert calls[1][2] == "warning"


def test_format_report_lists_beat_and_tasks() -> None:
    from celery.schedules import crontab

    from fastframe.tasks.listing import format_report

    class _App:
        class conf:
            beat_schedule = {
                "nightly": {
                    "task": "myapp.tasks.rebuild_report",
                    "schedule": crontab(hour=2, minute=0),
                    "args": (1,),
                },
                "tick": {"task": "myapp.tasks.tick", "schedule": 60},
            }

        tasks = {
            "celery.chord": object(),
            "myapp.tasks.rebuild_report": object(),
            "myapp.tasks.tick": object(),
        }

    text = format_report(_App())
    assert "Beat" in text.splitlines()[0]
    assert "nightly" in text
    assert "0 2 * * *" in text
    assert "args=(1,)" in text
    assert "every minute" in text
    assert "myapp.tasks.tick" in text
    assert "celery.chord" not in text
    tasks_at = text.index("Tasks")
    assert text.index("myapp.tasks.rebuild_report", tasks_at) > tasks_at


def test_format_report_is_empty_without_schedules_or_tasks() -> None:
    from fastframe.tasks.listing import format_report

    class _App:
        class conf:
            beat_schedule = {}

        tasks = {"celery.backend_cleanup": object()}

    assert format_report(_App()) == "Beat\n  (none)\n\nTasks\n  (none)"


def test_showtasks_prints_the_configured_schedule(miniproject_env, capsys) -> None:
    schedule = {"tick": {"task": "tests.tick", "schedule": 60, "kwargs": {"limit": 5}}}
    with _tasks_settings(eager=True, schedule=schedule):
        from celery import shared_task

        from fastframe.cli.commands.showtasks import execute

        @shared_task(name="tests.tick")
        def tick(limit: int) -> int:
            return limit

        execute(argparse.Namespace())
        out = capsys.readouterr().out
        assert "tick" in out
        assert "every minute" in out
        assert "tests.tick" in out
        assert "kwargs={'limit': 5}" in out
        assert "celery." not in out


def test_showtasks_refuses_when_tasks_are_not_installed(miniproject_env) -> None:
    from fastframe.cli.commands.showtasks import execute

    with _tasks_settings(eager=True, install=False):
        with pytest.raises(SystemExit, match="INSTALLED_APPS"):
            execute(argparse.Namespace())
