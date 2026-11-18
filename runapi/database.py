"""Async database support: engine/session management driven by ``DATABASE_URL``.

Requires SQLAlchemy (``pip install "runapi[sqlite]"`` or ``"runapi[postgres]"``). Typical use::

    # db.py
    from runapi import Database
    database = Database()                 # reads DATABASE_URL

    # main.py
    runapi_app.use_database(database)     # connect on startup, dispose on shutdown, /ready check

    # routes/items.py
    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from db import database

    async def get(session: AsyncSession = Depends(database.get_session)):
        ...
"""

import importlib.util
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional

from .config import RunApiConfig, get_config
from .errors import ConfigurationError

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
    from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine
    from sqlalchemy.orm import DeclarativeBase
    from sqlalchemy.pool import StaticPool

    DATABASE_AVAILABLE = True

    class Base(DeclarativeBase):
        """Declarative base for your models. Alembic autogenerate reads ``Base.metadata``."""

except ImportError:  # pragma: no cover - exercised only without SQLAlchemy installed
    DATABASE_AVAILABLE = False
    Base = None  # type: ignore[assignment,misc]

# async driver URL scheme -> (importable module, pip extra that installs it)
DRIVERS = {
    "postgresql+asyncpg": ("asyncpg", "postgres"),
    "sqlite+aiosqlite": ("aiosqlite", "sqlite"),
    "mysql+aiomysql": ("aiomysql", "mysql"),
}


def check_driver(url: str) -> None:
    """Raise ``ImportError`` with an install hint if SQLAlchemy or the URL's driver is missing."""
    if importlib.util.find_spec("sqlalchemy") is None:
        raise ImportError(
            'SQLAlchemy is not installed. Install with: pip install "runapi[sqlite]" '
            'or "runapi[postgres]"'
        )
    scheme = url.split("://", 1)[0].lower()
    if scheme in DRIVERS:
        module, extra = DRIVERS[scheme]
        if importlib.util.find_spec(module) is None:
            raise ImportError(
                f"The '{module}' driver needed by DATABASE_URL ({scheme}) is not installed. "
                f'Install with: pip install "runapi[{extra}]"'
            )


def _is_memory_sqlite(url: str) -> bool:
    return url.startswith("sqlite") and (":memory:" in url or "mode=memory" in url)


class Database:
    """Owns the async engine and hands out sessions.

    Sessions commit when the ``async with``/request finishes normally and roll back if an
    exception escapes, so route handlers do not need to manage transactions.
    """

    def __init__(
        self,
        url: Optional[str] = None,
        *,
        echo: Optional[bool] = None,
        config: Optional[RunApiConfig] = None,
        **engine_kwargs: Any,
    ):
        config = config or get_config()
        resolved = url or config.database_url
        if not resolved:
            raise ConfigurationError(
                "DATABASE_URL is not set, e.g. sqlite+aiosqlite:///./app.db "
                "or postgresql+asyncpg://user:password@localhost:5432/mydb"
            )
        self.url: str = resolved
        check_driver(self.url)
        self.echo = config.database_echo if echo is None else echo
        self._engine_kwargs = engine_kwargs
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None

    @property
    def engine(self) -> "AsyncEngine":
        if self._engine is None:
            raise RuntimeError("Database is not connected; call `await database.connect()`")
        return self._engine

    async def connect(self) -> None:
        """Create the engine (idempotent). Called automatically by ``use_database``."""
        if self._engine is not None:
            return
        kwargs = dict(self._engine_kwargs)
        if _is_memory_sqlite(self.url):
            # every new connection would otherwise get its own empty in-memory database
            kwargs.setdefault("poolclass", StaticPool)
            kwargs.setdefault("connect_args", {"check_same_thread": False})
        self._engine = _create_async_engine(self.url, echo=self.echo, **kwargs)
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    async def disconnect(self) -> None:
        """Close all pooled connections."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None

    async def ping(self) -> bool:
        """Readiness check: can we run ``SELECT 1``?"""
        async with self.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True

    @asynccontextmanager
    async def session(self) -> AsyncIterator["AsyncSession"]:
        """A session that commits on success and rolls back on error."""
        if self._sessionmaker is None:
            await self.connect()
        assert self._sessionmaker is not None
        async with self._sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                await session.rollback()
                raise

    async def get_session(self) -> AsyncIterator["AsyncSession"]:
        """FastAPI dependency: ``session: AsyncSession = Depends(database.get_session)``."""
        async with self.session() as session:
            yield session

    async def create_all(self) -> None:
        """Create tables from ``Base.metadata``. For quick starts and tests; use migrations
        (``runapi db migrate``) for real projects."""
        await self.connect()
        async with self.engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
