# Tutorial

FastFrame is a project workflow on top of FastAPI and SQLAlchemy. HTTP stays FastAPI. Data access stays SQLAlchemy. FastFrame owns apps, settings, migrations, and the `manage.py` loop.

## Create a project

```text
fastframe startproject myproject
cd myproject
python manage.py runserver
```

A generated project does not install admin, auth, the REST API, or Swagger. Add those later by listing them in `INSTALLED_APPS`. Swagger is `"fastframe.docs"`.

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

## Add an endpoint

Put this in `todos/api.py`. FastFrame mounts `api` from each installed app. The path is the string you write. It is not inferred from the class name.

```python
from fastframe.http import FastFrameAPI

api = FastFrameAPI()

@api.route("/todos")
class TodoAPI:
    def get(self):
        return Todo.objects.all()
```

A function route is the same idea: `@api.get("/todos")`. Request and response models come from `fastframe.schemas` (`BaseModel`, `Field`), which are Pydantic's classes. A native `APIRouter` in `todos/urls.py` still works. See [API](api-layer.md).

`/docs` is not on unless you add `"fastframe.docs"` to `INSTALLED_APPS`.

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
