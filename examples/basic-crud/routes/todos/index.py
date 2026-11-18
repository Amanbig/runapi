"""/todos  ->  GET (list), POST (create)

The folder name is the URL, `index.py` is the folder's root, and function names are
HTTP methods.
"""

from typing import Optional

from fastapi.encoders import jsonable_encoder
from schemas.todo import TodoCreate
from services import todo as todos

from runapi import JSONResponse


async def get(done: Optional[bool] = None):
    """GET /todos?done=true"""
    return await todos.list_todos(done)


async def post(body: TodoCreate):
    created = await todos.create_todo(body.model_dump())
    return JSONResponse(jsonable_encoder(created), status_code=201)
