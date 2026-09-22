from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from fastframe.http.pagination import Pagination, pagination
from todos.models import Todo

router = APIRouter(prefix="/todos", tags=["todos"])


class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    done: bool


@router.get("", response_model=list[TodoOut])
def list_todos(
    done: bool | None = None,
    page: Pagination = Depends(pagination),
) -> list[Todo]:
    """List todos, optionally filtered by completion status.

    Supports `?limit=&offset=` pagination (default limit 20, max 100).
    """
    qs = Todo.objects.all().order_by("-created_at")
    if done is not None:
        qs = qs.filter(done=done)
    return list(page.apply(qs))


@router.post("", response_model=TodoOut, status_code=201)
def create_todo(payload: TodoCreate) -> Todo:
    return Todo.objects.create(title=payload.title, done=False)


@router.get("/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int) -> Todo:
    """DoesNotExist is auto-converted to 404 by the framework."""
    return Todo.objects.get(id=todo_id)


@router.patch("/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, payload: TodoUpdate) -> Todo:
    todo = Todo.objects.get(id=todo_id)
    if payload.title is not None:
        todo.title = payload.title
    if payload.done is not None:
        todo.done = payload.done
    todo.save()
    return todo


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int) -> None:
    todo = Todo.objects.get(id=todo_id)
    todo.delete()
