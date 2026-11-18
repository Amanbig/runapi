import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from typer.testing import CliRunner

from runapi import ConfigurationError, Database, check_driver, create_runapi_app
from runapi.cli import app as cli_app
from runapi.config import RunApiConfig, load_config

runner = CliRunner()
MEMORY = "sqlite+aiosqlite:///:memory:"


def run(coro):
    return asyncio.run(coro)


def test_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        Database(config=RunApiConfig())


def test_reads_url_from_config(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", MEMORY)
    assert Database(config=RunApiConfig()).url == MEMORY


@pytest.mark.parametrize(
    "url, module, extra",
    [
        ("postgresql+asyncpg://u:p@h/db", "asyncpg", "postgres"),
        ("sqlite+aiosqlite:///x.db", "aiosqlite", "sqlite"),
        ("mysql+aiomysql://u:p@h/db", "aiomysql", "mysql"),
    ],
)
def test_check_driver_gives_install_hint(monkeypatch, url, module, extra):
    import importlib.util as util

    real = util.find_spec
    monkeypatch.setattr(util, "find_spec", lambda n, *a: None if n == module else real(n, *a))
    with pytest.raises(ImportError) as exc:
        check_driver(url)
    assert f"runapi[{extra}]" in str(exc.value)


def test_check_driver_ok_for_installed_driver():
    check_driver(MEMORY)  # does not raise


def test_session_commits_and_rolls_back():
    async def scenario():
        db = Database(MEMORY, config=RunApiConfig())
        await db.connect()
        try:
            async with db.engine.begin() as conn:
                await conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)"))

            async with db.session() as s:
                await s.execute(text("INSERT INTO t (v) VALUES ('kept')"))

            with pytest.raises(ValueError):
                async with db.session() as s:
                    await s.execute(text("INSERT INTO t (v) VALUES ('lost')"))
                    raise ValueError("boom")

            async with db.session() as s:
                rows = (await s.execute(text("SELECT v FROM t"))).scalars().all()
            return rows
        finally:
            await db.disconnect()

    # in-memory SQLite must share one connection or tables would vanish between sessions
    assert run(scenario()) == ["kept"]


def test_engine_requires_connect_and_disconnect_is_safe():
    db = Database(MEMORY, config=RunApiConfig())
    with pytest.raises(RuntimeError, match="not connected"):
        _ = db.engine
    run(db.disconnect())  # no-op when never connected


def test_ping_and_connect_idempotent():
    async def scenario():
        db = Database(MEMORY, config=RunApiConfig())
        await db.connect()
        engine = db.engine
        await db.connect()
        assert db.engine is engine
        ok = await db.ping()
        await db.disconnect()
        return ok

    assert run(scenario()) is True


def test_create_all_creates_tables():
    from sqlalchemy import String
    from sqlalchemy.orm import Mapped, mapped_column

    from runapi import Base

    class Thing(Base):
        __tablename__ = "things_create_all_test"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str] = mapped_column(String(10))

    async def scenario():
        db = Database(MEMORY, config=RunApiConfig())
        try:
            await db.create_all()
            async with db.session() as s:
                s.add(Thing(name="x"))
            async with db.session() as s:
                return (
                    (await s.execute(text("SELECT name FROM things_create_all_test")))
                    .scalars()
                    .all()
                )
        finally:
            await db.disconnect()

    try:
        assert run(scenario()) == ["x"]
    finally:
        Base.metadata.remove(Thing.__table__)


def test_use_database_wires_lifecycle_and_readiness(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "a-very-long-random-secret-key-for-tests-0123456789")
    load_config()
    db = Database(MEMORY, config=RunApiConfig())
    runapi_app = create_runapi_app()
    runapi_app.use_database(db)
    with TestClient(runapi_app.get_app()) as client:
        assert client.get("/ready").json() == {"status": "ready", "checks": {"database": True}}
    assert db._engine is None  # disposed on shutdown


def test_readiness_fails_when_database_unreachable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "a-very-long-random-secret-key-for-tests-0123456789")
    load_config()
    db = Database(f"sqlite+aiosqlite:///{tmp_path}/missing/dir/x.db", config=RunApiConfig())
    runapi_app = create_runapi_app()
    runapi_app.add_readiness_check("database", db.ping)  # never connected -> RuntimeError
    client = TestClient(runapi_app.get_app())
    assert client.get("/ready").status_code == 503


# ---- CLI --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "db, expected_url", [("sqlite", "sqlite+aiosqlite"), ("postgres", "postgresql+asyncpg")]
)
def test_init_with_database(tmp_path, monkeypatch, db, expected_url):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli_app, ["init", "app", "--db", db])
    assert result.exit_code == 0, result.output
    root = tmp_path / "app"
    for rel in [
        "db.py",
        "models/item.py",
        "alembic.ini",
        "migrations/env.py",
        "migrations/script.py.mako",
        "migrations/versions",
        "routes/api/items.py",
    ]:
        assert (root / rel).exists(), rel
    assert f"DATABASE_URL={expected_url}" in (root / ".env").read_text()
    assert (root / "requirements.txt").read_text().startswith(f"runapi[{db}]")
    assert (root / "docker-compose.yml").exists() is (db == "postgres")
    assert "use_database" in (root / "main.py").read_text()


def test_init_rejects_unknown_database(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli_app, ["init", "app", "--db", "oracle"])
    assert result.exit_code == 1 and "--db must be one of" in result.output
    assert not (tmp_path / "app").exists()


def test_db_init_in_existing_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(cli_app, ["db", "init"]).exit_code == 0
    assert (tmp_path / "alembic.ini").exists()
    assert (tmp_path / "models" / "__init__.py").exists()
    again = runner.invoke(cli_app, ["db", "init"])
    assert again.exit_code == 1 and "already exists" in again.output


def test_doctor_reports_missing_driver(tmp_path, monkeypatch):
    import importlib.util as util

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "a-very-long-random-secret-key-for-tests-0123456789")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://u:p@localhost/db")
    (tmp_path / "main.py").write_text("")
    (tmp_path / "routes").mkdir()
    real = util.find_spec
    monkeypatch.setattr(util, "find_spec", lambda n, *a: None if n == "asyncpg" else real(n, *a))
    result = runner.invoke(cli_app, ["doctor"])
    assert result.exit_code == 1
    assert "runapi[postgres]" in result.output
