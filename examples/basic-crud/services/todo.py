"""Business rules live here, between the routes and the repository."""

from repositories.todo import TodoRepository

from runapi import NotFoundError, ValidationError

_repository = TodoRepository()  # one shared instance: imports are cached, so routes share it


async def list_todos(done=None):
    filters = {} if done is None else {"done": done}
    return await _repository.get_all(**filters)


async def get_todo(todo_id: int):
    todo = await _repository.get(todo_id)
    if todo is None:
        raise NotFoundError(f"Todo {todo_id} not found")
    return todo


async def create_todo(data: dict):
    if data["title"].strip().lower() == "todo":
        raise ValidationError("Please give the todo a more specific title")
    return await _repository.create(data)


async def update_todo(todo_id: int, data: dict):
    await get_todo(todo_id)  # 404 if it does not exist
    return await _repository.update(todo_id, data)


async def delete_todo(todo_id: int):
    await get_todo(todo_id)
    await _repository.delete(todo_id)
