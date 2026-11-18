"""GET / PUT / DELETE /todos/{id}"""

from typing import Optional

from db import database
from fastapi import Depends, HTTPException, Response
from models.todo import Todo
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    done: Optional[bool] = None


async def _get_or_404(session: AsyncSession, id: int) -> Todo:
    todo = await session.get(Todo, id)
    if todo is None:
        raise HTTPException(status_code=404, detail=f"Todo {id} not found")
    return todo


def serialize(todo: Todo) -> dict:
    return {"id": todo.id, "title": todo.title, "done": todo.done}


async def get(id: int, session: AsyncSession = Depends(database.get_session)):
    return serialize(await _get_or_404(session, id))


async def put(id: int, body: TodoUpdate, session: AsyncSession = Depends(database.get_session)):
    todo = await _get_or_404(session, id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(todo, field, value)
    return serialize(todo)


async def delete(id: int, session: AsyncSession = Depends(database.get_session)):
    await session.delete(await _get_or_404(session, id))
    return Response(status_code=204)
