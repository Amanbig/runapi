"""Data access. InMemoryRepository keeps rows in a dict, so data is lost on restart.

For a database, swap in SQLAlchemyRepository (see `pip install runapi[db]`).
"""

from runapi import InMemoryRepository


class TodoRepository(InMemoryRepository):
    pass
