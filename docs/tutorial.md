# Tutorial

FastFrame is a project workflow on top of FastAPI and SQLAlchemy. HTTP stays FastAPI. Data access stays SQLAlchemy. FastFrame owns apps, settings, migrations, and the `manage.py` loop.

## Create a project

```text
fastframe startproject myproject
cd myproject
python manage.py runserver
```

A generated project does not install admin, auth, or the REST API. Add those later by listing them in `INSTALLED_APPS`.

## Add an app and a model

```text
python manage.py startapp todos
```

```python
from fastframe.models import Model, fields

class Todo(Model):
    title = fields.CharField(max_length=200)
    done = fields.BooleanField(default=False)

    class Meta:
        db_table = "todos"
```

Add `"todos"` to `INSTALLED_APPS`, then:

```text
python manage.py makemigrations
python manage.py migrate
```

Routes are normal FastAPI routers. Export one from `todos/urls.py` and FastFrame mounts it.

## Day-to-day commands

```text
python manage.py showmigrations
python manage.py shell
python manage.py dbshell
python manage.py test -v
python manage.py check --database
```

## Next

- [CLI](cli.md) for every command.
- [Fields](models-fields-design.md) and [queries](orm-features.md) for models.
- [Admin](admin-setup.md) and [auth](auth.md) when you want them.
- [Settings](settings.md) for the knobs that exist.
