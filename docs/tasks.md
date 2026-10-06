# Background jobs

Background jobs are Celery. FastFrame does not ship a second queue.

Add the app and install Celery:

```text
pip install "fast-frame[tasks]"
```

```python
INSTALLED_APPS = [
    "fastframe.tasks",
    "myapp",
]
```

A new project does not include `fastframe.tasks`. Leaving it out means none of this runs.

## A task

A task is Celery's `@shared_task` on a normal sync function. Calling the function runs it in the current process. `.delay()` publishes a message and returns.

```python
from celery import shared_task


@shared_task
def rebuild_report(report_id: int) -> None: ...


rebuild_report.delay(report_id)
```

Arguments must be JSON-serializable. Chains, chords, and retries are Celery's. FastFrame does not wrap them.

The task body runs in its own database session, not the request's session. The session commits if the task returns and rolls back if the task raises. See [session-lifecycle.md](session-lifecycle.md).

Put tasks in an installed app's `tasks.py`. FastFrame imports that module when the tasks app starts.

## Broker

Celery needs a broker. The default is Redis:

```python
CELERY_BROKER_URL = "redis://localhost:6379/0"
```

RabbitMQ is the same setting with a different URL. There is no database-table queue.

`CELERY_RESULT_BACKEND` is optional. Leave it unset unless you call `.get()` on a result from another process.

## Worker and Beat

```text
python manage.py work
python manage.py beat
python manage.py showtasks
```

`work` starts a Celery worker. Run as many workers as you need.

`beat` starts Celery Beat. Beat only enqueues periodic tasks. A worker runs them. Run one Beat process. Schedules live in `CELERY_BEAT_SCHEDULE`:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    "rebuild-nightly": {
        "task": "myapp.tasks.rebuild_report",
        "schedule": crontab(hour=2, minute=0),
        "args": (1,),
    },
}
```

`schedule` may also be a number of seconds.

`showtasks` prints that schedule and the task names a worker will run. It reads the configuration in this process. It does not start Beat or a worker, and it does not connect to the broker, so it does not list processes that are already up.

```text
Beat
  nightly  0 2 * * *     myapp.tasks.rebuild_report  args=(1,)
  tick     every minute  myapp.tasks.tick

Tasks
  myapp.tasks.rebuild_report
  myapp.tasks.tick
```

An interval prints as `every minute` or `every 24 hours`. A crontab prints as the five-field expression, `0 2 * * *`. Celery's own tasks (`celery.*`) are left out.

## Tests

Set `CELERY_TASK_ALWAYS_EAGER = True`. `.delay()` then runs the task in-process. Tests do not start a worker, Beat, or Redis. `manage.py check` does not require `CELERY_BROKER_URL` while eager mode is on.
