from sqlalchemy import Boolean, String, false
from sqlalchemy.orm import Mapped, mapped_column

from runapi import Base


class Todo(Base):
    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    done: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
