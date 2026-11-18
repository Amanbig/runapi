"""/todos/{id}  ->  GET, PUT, DELETE

`[id].py` is a dynamic segment: the value arrives as the `id` argument.
"""

from fastapi import Response
from schemas.todo import TodoUpdate
from services import todo as todos


async def get(id: int):
    return await todos.get_todo(id)


async def put(id: int, body: TodoUpdate):
    return await todos.update_todo(id, body.model_dump(exclude_unset=True))


async def delete(id: int):
    await todos.delete_todo(id)
    return Response(status_code=204)
