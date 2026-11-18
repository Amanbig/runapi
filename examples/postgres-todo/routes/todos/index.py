"""GET /todos (optionally ?done=true), POST /todos"""

from typing import Optional

from db import database
from fastapi import Depends
from models.todo import Todo
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    done: bool = False


def serialize(todo: Todo) -> dict:
    return {"id": todo.id, "title": todo.title, "done": todo.done}


async def get(done: Optional[bool] = None, session: AsyncSession = Depends(database.get_session)):
    query = select(Todo).order_by(Todo.id)
    if done is not None:
        query = query.where(Todo.done == done)
    return [serialize(t) for t in (await session.execute(query)).scalars()]


async def post(body: TodoCreate, session: AsyncSession = Depends(database.get_session)):
    todo = Todo(title=body.title, done=body.done)
    session.add(todo)
    await session.flush()  # assigns todo.id; the session commits when the request finishes
    return serialize(todo)
