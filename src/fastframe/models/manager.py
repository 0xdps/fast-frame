from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select

from fastframe.db.session import get_current_session
from fastframe.models.exceptions import DoesNotExist, MultipleObjectsReturned

T = TypeVar("T")


class Manager(Generic[T]):
    def __init__(self, model_class: type[T]) -> None:
        self.model_class = model_class

    @property
    def session(self):
        return get_current_session()

    def all(self) -> list[T]:
        stmt = select(self.model_class)
        return list(self.session.scalars(stmt).all())

    def filter(self, **kwargs: Any) -> list[T]:
        stmt = select(self.model_class)
        for key, value in kwargs.items():
            stmt = stmt.where(getattr(self.model_class, key) == value)
        return list(self.session.scalars(stmt).all())

    def get(self, **kwargs: Any) -> T:
        matches = self.filter(**kwargs)
        if not matches:
            raise DoesNotExist(f"{self.model_class.__name__} matching {kwargs!r} does not exist.")
        if len(matches) > 1:
            raise MultipleObjectsReturned(
                f"{self.model_class.__name__} matching {kwargs!r} returned {len(matches)} rows."
            )
        return matches[0]

    def first(self) -> T | None:
        stmt = select(self.model_class).limit(1)
        return self.session.scalars(stmt).first()

    def count(self) -> int:
        stmt = select(func.count()).select_from(self.model_class)
        result = self.session.scalar(stmt)
        return int(result or 0)

    def create(self, **kwargs: Any) -> T:
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance
