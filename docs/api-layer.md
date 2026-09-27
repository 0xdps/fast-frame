# API

FastFrame adds a routing facade. It does not replace FastAPI.

```python
from fastframe.http import FastFrameAPI
from fastframe.schemas import BaseModel, Field

api = FastFrameAPI()
```

`BaseModel` and `Field` are Pydantic's, re-exported from `fastframe.schemas`. They are not a subclass, and they are not a second validator. Import from `pydantic` when you need a name that module does not list. `fastframe.api` is the optional token REST app, not this facade.

Three styles are valid in the same project.

## Resource

The path is explicit. `UserAPI` does not become `/users`.

```python
@api.route("/users/{id}")
class UserAPI:
    def get(self, id: int):
        return User.objects.get(id=id)

    def delete(self, id: int):
        user = User.objects.get(id=id)
        user.delete()
        return {"deleted": True}
```

Methods named `get`, `post`, `put`, `patch`, or `delete` become routes. Any other method is ignored.

## Function

```python
class UserCreate(BaseModel):
    name: str
    age: int = Field(ge=18)

@api.get("/users")
def get_users():
    return User.objects.all()

@api.post("/users")
def create_user(data: UserCreate):
    return User.objects.create(**data.model_dump())
```

`response_model=`, `tags=`, and `Depends` are forwarded to FastAPI. OpenAPI comes from FastAPI. There is no second docs system. `Depends` is still imported from `fastapi`.

Returning a `Model` or a `QuerySet` serializes its fields to JSON. Return a dict, or set `response_model`, when you want a different shape.

## Native FastAPI

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/payments")
def payments():
    ...

api.include_router(router)
```

`api.router` is the underlying `APIRouter` if you would rather mount it yourself from `urls.py`.

## Where it is mounted

An installed app may define `api` in `<app>.api`. FastFrame mounts that router next to the app's `urls.py` router. A missing `api.py` is fine. Nothing is imported for an app that is not in `INSTALLED_APPS`.

Swagger is also an app. Add `"fastframe.docs"` to `INSTALLED_APPS` and FastAPI serves `/docs`. Leave it out and that route does not exist.
