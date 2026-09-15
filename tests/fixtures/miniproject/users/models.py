from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastframe.models import Model


class User(Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationship to posts
    posts: Mapped[list["Post"]] = relationship("Post", back_populates="author")  # type: ignore[name-defined] # noqa: F821, UP037
