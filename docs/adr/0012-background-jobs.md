# ADR 0012: Background jobs, and no email or storage batteries

## Status

Accepted. Not implemented. The next battery to build. See [the roadmap](../roadmap.md).

## Context

Phases 1 through 4.5 shipped the project loop, admin, auth, and the token API. The old Phase 6 list bundled background tasks with email, caching, and storage (`FileField` / `ImageField`).

Email and storage come off that list. Mail and file storage are products of their own, and a framework wrapper around them would be a second API in front of libraries people already pick (an SMTP client, boto3, a local directory). Caching, signals, and a custom management-command loader stay on the plan. They are later work, not part of this app. Background work is the piece to build now: a request should be able to enqueue a function and return, and a separate process should run it, using the same sync ORM as the rest of FastFrame ([ADR 0006](0006-sync-sqlalchemy-for-v0-1.md)). The queue is Celery. It is the usual Python worker, and FastFrame will not grow a second one.

[ADR 0005](0005-extensibility-via-installed-apps.md) left storage backends "deferred until needed." That wait is over as a decision: we will not add them. The Addition on 0005 records the withdrawal. This ADR is the plan for jobs.

## Decision

### Out of scope

- No email battery. No `send_mail`, no mail backend setting, no template-for-mail API. A task may call any mail library the project installed. FastFrame will not.
- No storage battery. No storage backend protocol, no `FileField`, no `ImageField`. A project that needs files uses its own library and stores a path or URL on a normal field.

### What a job is

An optional app, `fastframe.tasks`, mounted only when it is listed in `INSTALLED_APPS`. A new project does not include it. Celery is installed with that app, not with the base `fast-frame` package.

A task is Celery's `@shared_task` on a normal sync function. Calling the function runs it in the current process. `.delay()` publishes a message and returns.

```python
from celery import shared_task


@shared_task
def rebuild_report(report_id: int) -> None: ...


rebuild_report.delay(report_id)
```

FastFrame does not wrap `delay`, chains, chords, or retries. Those are Celery's. The task body that touches the database opens its own session. It does not reuse the request session. See [session-lifecycle.md](../session-lifecycle.md).

### The broker

Celery needs a broker. The documented default is Redis (`CELERY_BROKER_URL`). RabbitMQ is a Celery configuration change, not a FastFrame queue. There is no database-table queue and no FastFrame broker protocol.

Messages use Celery's JSON serializer.

### Processes

`python manage.py work` starts a Celery worker. `python manage.py beat` starts Celery Beat, the clock that enqueues periodic tasks. Beat does not run the function. One Beat process is enough. Workers are separate processes, and you can run more than one.

Periodic schedules live in Celery Beat's configuration. FastFrame does not ship a second scheduler.

### Tests

Celery's eager mode runs `delay` in-process. Tests turn that on. They do not start a worker or Beat.

## Consequences

- Phase 6 on the roadmap is this app, and it is the next work. Templates and static files stay planned and are not this phase.
- A project that uses tasks runs Redis (or another Celery broker) beside the app. The database remains the system of record for models, not the job queue.
- Email and object storage are non-goals, not a later phase. `FileField` and `ImageField` are not planned.
- Caching, signals, and a custom management-command loader stay planned. They are later than this app, and they are not part of `fastframe.tasks`.
- Chains, chords, retries, and Beat are Celery features a project may use. FastFrame does not reimplement them and does not hide them behind another API.
