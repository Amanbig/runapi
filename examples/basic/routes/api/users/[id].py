from fastapi import HTTPException
from routes.api.users.index import USERS


async def get(id: int):
    if id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    return USERS[id]
