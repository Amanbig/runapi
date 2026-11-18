USERS = {1: {"id": 1, "name": "Ada"}, 2: {"id": 2, "name": "Linus"}}


async def get():
    return list(USERS.values())
