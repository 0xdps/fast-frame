"""Print the Beat schedule and the tasks a worker will run.

This reads the Celery app configured in the current process. It does not
start a worker or Beat, and it does not connect to the broker.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any


def show_tasks() -> None:
    """Bootstrap and print Beat entries and registered task names."""
    from fastframe.tasks.runtime import load_app

    print(format_report(load_app()))


def format_report(app: Any) -> str:
    """Return the Beat schedule and registered tasks as plain text."""
    lines = ["Beat", *_beat_lines(app), "", "Tasks", *_task_lines(app)]
    return "\n".join(lines)


def describe_schedule(schedule: object) -> str:
    """Turn a Beat schedule value into a short label."""
    if isinstance(schedule, (int, float)) and not isinstance(schedule, bool):
        return _every(float(schedule))
    run_every = getattr(schedule, "run_every", None)
    if isinstance(run_every, timedelta):
        return _every(run_every.total_seconds())
    text = str(schedule)
    marker = "<crontab: "
    if text.startswith(marker) and text.endswith(">"):
        body = text[len(marker) : -1]
        expr, separator, _legend = body.rpartition(" (")
        return expr if separator else body
    return text


def _every(seconds: float) -> str:
    steps = (
        (86400, "day", "days"),
        (3600, "hour", "hours"),
        (60, "minute", "minutes"),
    )
    for size, one, many in steps:
        if seconds >= size and seconds % size == 0:
            count = int(seconds // size)
            if count == 1:
                return f"every {one}"
            return f"every {count} {many}"
    if seconds == 1:
        return "every second"
    return f"every {seconds:g} seconds"


def _beat_lines(app: Any) -> list[str]:
    schedule = dict(getattr(app.conf, "beat_schedule", None) or {})
    if not schedule:
        return ["  (none)"]
    rows = [_beat_row(name, schedule[name]) for name in sorted(schedule)]
    name_width = max(len(name) for name, _, _ in rows)
    when_width = max(len(when) for _, when, _ in rows)
    return [_beat_line(name, when, detail, name_width, when_width) for name, when, detail in rows]


def _beat_row(name: str, entry: object) -> tuple[str, str, str]:
    if not isinstance(entry, dict):
        return name, describe_schedule(entry), ""
    task = str(entry.get("task", ""))
    extra: list[str] = []
    if entry.get("args"):
        extra.append(f"args={entry['args']!r}")
    if entry.get("kwargs"):
        extra.append(f"kwargs={entry['kwargs']!r}")
    detail = task if not extra else f"{task}  {' '.join(extra)}"
    return name, describe_schedule(entry.get("schedule", "")), detail


def _beat_line(name: str, when: str, detail: str, name_width: int, when_width: int) -> str:
    return f"  {name:<{name_width}}  {when:<{when_width}}  {detail}".rstrip()


def _task_lines(app: Any) -> list[str]:
    names = sorted(name for name in app.tasks if not str(name).startswith("celery."))
    if not names:
        return ["  (none)"]
    return [f"  {name}" for name in names]
