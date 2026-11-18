"""End to end: run the PostgreSQL example's migrations and CRUD against a real database.

SQLite always runs. PostgreSQL runs when POSTGRES_TEST_URL is set (CI provides a service
container), e.g. POSTGRES_TEST_URL=postgresql+asyncpg://app:app@localhost:5432/app
"""

import os
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from runapi.cli import app as cli_app
from runapi.config import load_config

EXAMPLE = Path(__file__).parent.parent / "examples" / "postgres-todo"
runner = CliRunner()

URLS = ["sqlite"]
if os.environ.get("POSTGRES_TEST_URL"):
    URLS.append("postgres")


def _purge_modules():
    """Forget the example's modules (and its models) so each test imports a fresh copy."""
    from runapi import Base

    for name in [m for m in sys.modules if m.split(".")[0] in {"routes", "models", "db", "main"}]:
        del sys.modules[name]
    Base.registry.dispose()
    Base.metadata.clear()


@pytest.fixture(params=URLS)
def project(request, tmp_path, monkeypatch):
    work = tmp_path / "todo"
    shutil.copytree(EXAMPLE, work, ignore=shutil.ignore_patterns("__pycache__", ".env"))
    if request.param == "sqlite":
        url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    else:
        url = os.environ["POSTGRES_TEST_URL"]
    monkeypatch.chdir(work)
    monkeypatch.syspath_prepend(str(work))
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.setenv("SECRET_KEY", "example-test-secret-key-0123456789abcdef")
    _purge_modules()
    load_config()
    yield work
    runner.invoke(cli_app, ["db", "downgrade", "base"])  # leave a shared database clean
    _purge_modules()


def test_migrate_and_crud(project):
    upgrade = runner.invoke(cli_app, ["db", "upgrade"])
    assert upgrade.exit_code == 0, upgrade.output

    import main  # the example's main.py wires database -> startup/shutdown/readiness

    with TestClient(main.app) as client:
        assert client.get("/ready").json()["checks"] == {"database": True}
        assert client.get("/todos").json() == []

        created = client.post("/todos", json={"title": "write docs"})
        assert created.status_code == 200
        todo = created.json()
        assert todo == {"id": todo["id"], "title": "write docs", "done": False}

        updated = client.put(f"/todos/{todo['id']}", json={"done": True}).json()
        assert updated["done"] is True
        assert [t["id"] for t in client.get("/todos", params={"done": True}).json()] == [todo["id"]]
        assert client.get("/todos", params={"done": False}).json() == []

        assert client.post("/todos", json={"title": ""}).status_code == 422
        assert client.get("/todos/99999").status_code == 404

        assert client.delete(f"/todos/{todo['id']}").status_code == 204
        assert client.get(f"/todos/{todo['id']}").status_code == 404


def test_failed_request_rolls_back(project):
    from models.todo import Todo
    from sqlalchemy import select

    assert runner.invoke(cli_app, ["db", "upgrade"]).exit_code == 0
    import asyncio

    from db import database

    async def scenario():
        await database.connect()
        try:
            with pytest.raises(RuntimeError):
                async with database.session() as session:
                    session.add(Todo(title="never saved"))
                    await session.flush()
                    raise RuntimeError("boom")
            async with database.session() as session:
                return (await session.execute(select(Todo))).scalars().all()
        finally:
            await database.disconnect()

    assert asyncio.run(scenario()) == []
