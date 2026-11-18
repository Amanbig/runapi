# Schemas & storage

## Schemas

Any `*.py` file under `schemas/` is imported at startup and every public Pydantic model in it is
registered by name:

```python
# schemas/user.py
from runapi import BaseSchema


class UserCreate(BaseSchema):
    name: str
```

```python
from runapi import get_schema, list_schemas

get_schema("UserCreate")  # short name
get_schema("schemas.user.UserCreate")  # full path (nested folders become dots)
list_schemas()
```

Things to know:

- Names starting with `_` and non-Pydantic classes are ignored.
- Files load in alphabetical order. If two files define the same class name, a warning is logged,
  the **later file wins the short name**, and both stay reachable by their full path.
- A schema file that fails to import is logged as an error; other schemas still load.
- Built-ins: `BaseSchema`, `IDMixin`, `TimestampMixin`, `PaginationParams`, `PaginatedResponse`.
- `runapi schemas` lists what was discovered.

## Storage modes

| Mode | Use for | Persistence | Multiple workers |
|------|---------|-------------|------------------|
| `InMemoryRepository` (default, no extra install) | prototypes, tests | lost on restart | each worker has its own copy |
| `SQLAlchemyRepository` / `Database` + `runapi[sqlite]` | local apps, tests | file on disk | safe for reads; SQLite serialises writes |
| `Database` + `runapi[postgres]` | production | durable | yes |

**Without SQLAlchemy installed** runapi still imports and runs: `InMemoryRepository` works,
`SQLAlchemyRepository` is `None`, and `Database(...)` raises an error telling you which extra to install.

**In-memory limits:** data disappears on restart, is not shared between worker processes, and has no
transactions or constraints. Do not run it in production with `WORKERS > 1`.

## Repositories

```python
from runapi import InMemoryRepository


class WidgetRepository(InMemoryRepository): ...


repo = WidgetRepository()
item = await repo.create({"name": "gear"})  # adds an `id`
await repo.get_all(skip=0, limit=10, name="gear")
```

`SQLAlchemyRepository(session, Model)` has the same methods, so you can swap storage without
changing your service layer. See [Database & migrations](database.md) for sessions.
