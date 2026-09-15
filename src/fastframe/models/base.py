from __future__ import annotations

from typing import Any, ClassVar

from sqlalchemy.orm import DeclarativeBase

from fastframe.models.manager import Manager


class Model(DeclarativeBase):
    """SQLAlchemy declarative base with a thin Django-like manager."""

    objects: ClassVar[Manager[Any]]

    def __repr__(self) -> str:
        """Return a Django-style repr showing primary key and attributes."""
        attrs = []
        for col in self.__table__.columns:
            val = getattr(self, col.name, None)
            if isinstance(val, str):
                val = repr(val)
            attrs.append(f"{col.name}={val}")
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"

    def save(self) -> None:
        from fastframe.db.session import get_current_session

        session = get_current_session()
        session.add(self)
        session.flush()

    def delete(self) -> None:
        from fastframe.db.session import get_current_session

        session = get_current_session()
        session.delete(self)
        session.flush()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not Model and getattr(cls, "__tablename__", None):
            cls.objects = Manager(cls)
