# Database & migrations

runapi uses async SQLAlchemy and Alembic. Pick the extra for your database; the code is the same
for all of them and only `DATABASE_URL` changes.

| Extra | Driver | `DATABASE_URL` |
|-------|--------|----------------|
| `runapi[sqlite]` | aiosqlite | `sqlite+aiosqlite:///./app.db` |
| `runapi[postgres]` | asyncpg | `postgresql+asyncpg://user:password@localhost:5432/mydb` |
| `runapi[mysql]` | aiomysql | `mysql+aiomysql://user:password@localhost:3306/mydb` |

(`runapi[db]` is kept as an alias for the SQLite stack.) `runapi doctor` tells you which extra to
install if the driver for your `DATABASE_URL` is missing.

## Quick start

```bash
pip install "runapi[postgres]"
runapi init my-api --db postgres      # or --db sqlite
cd my-api
docker compose up -d db               # PostgreSQL (skip for SQLite)
runapi db migrate -m "create items"
runapi db upgrade
runapi dev
```

`--db` generates `models/`, `db.py`, `alembic.ini`, `migrations/`, an example route and (for
PostgreSQL) a `docker-compose.yml`. For an existing project run `runapi db init`.

## Sessions in your routes

```python
# db.py
from runapi import Database

database = Database()  # reads DATABASE_URL

# main.py
runapi_app.use_database(database)  # connect on startup, dispose on shutdown, /ready check

# routes/items.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from db import database


async def post(body: ItemCreate, session: AsyncSession = Depends(database.get_session)):
    item = Item(name=body.name)
    session.add(item)
    await session.flush()  # assigns item.id
    return {"id": item.id}  # the session commits when the request finishes
```

The session **commits when the request succeeds and rolls back if an exception escapes**, so
handlers do not manage transactions. Outside a request use `async with database.session() as s:`.

Define models on `runapi.Base` and import them in `models/__init__.py` so Alembic can see them.

## Migrations

```bash
runapi db migrate -m "add due date"   # autogenerate from model changes; review the result
runapi db upgrade                     # apply (default: head)
runapi db downgrade                   # revert one step (or: runapi db downgrade base)
```

`migrations/env.py` reads `DATABASE_URL` and `Base.metadata`. Generate migrations against the
database you deploy to, because SQLite renders some defaults differently from PostgreSQL.

## Working example

[`examples/postgres-todo`](https://github.com/Amanbig/runapi/tree/main/examples/postgres-todo) is a
complete todo API with a committed migration. CI runs it against a real PostgreSQL service and
against SQLite.

## Repositories

If you prefer the repository pattern, `SQLAlchemyRepository(session, Model)` wraps a session with
`get`, `get_all`, `create`, `update`, `delete` and `count`. See [Schemas & storage](storage.md).
