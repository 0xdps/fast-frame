from __future__ import annotations

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastframe.models import Model


class Post(Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # SQLAlchemy relationship (escape hatch example)
    author: Mapped["User"] = relationship(  # noqa: F821, UP037
        lambda: __import__("users.models", fromlist=["User"]).User,
        back_populates="posts",
    )
