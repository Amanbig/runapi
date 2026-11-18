"""Alembic environment: async engine, URL from DATABASE_URL, models from `Base.metadata`."""

import asyncio

import models  # noqa: F401  (importing the package registers every model on Base.metadata)
from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from runapi import Base
from runapi.config import load_config

config = context.config
target_metadata = Base.metadata


def _database_url() -> str:
    url = load_config().database_url
    if not url:
        raise SystemExit(
            "DATABASE_URL is not set, e.g. sqlite+aiosqlite:///./app.db "
            "or postgresql+asyncpg://user:password@localhost:5432/mydb"
        )
    return url


def run_migrations_offline() -> None:
    """Emit SQL to stdout instead of connecting (`alembic upgrade head --sql`)."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run_sync_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=True,  # lets SQLite alter tables; harmless on PostgreSQL
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    engine = create_async_engine(_database_url())
    async with engine.connect() as connection:
        await connection.run_sync(_run_sync_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
