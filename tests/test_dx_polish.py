import pytest
from fastapi.testclient import TestClient

from runapi import create_runapi_app
from runapi.config import RunApiConfig, load_config

SECRET = "a-very-long-random-secret-key-for-tests-0123456789"


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for key in ["ENVIRONMENT", "DEBUG", "LOG_REQUESTS", "DATABASE_URL"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SECRET_KEY", SECRET)
    load_config()
    (tmp_path / "routes").mkdir()
    return tmp_path


def test_warns_when_route_file_has_no_handlers(project):
    (project / "routes" / "empty.py").write_text("x = 1\n")
    app = create_runapi_app()
    assert len(app.route_warnings) == 1
    assert "defines no handlers" in app.route_warnings[0]
    assert "/empty" in app.route_warnings[0]


def test_suggests_rename_for_misnamed_handlers(project):
    (project / "routes" / "users.py").write_text(
        "async def GET():\n    return {}\n\nasync def get_users():\n    return {}\n"
    )
    app = create_runapi_app()
    warning = app.route_warnings[0]
    assert "GET" in warning and "get_users" in warning
    assert TestClient(app.get_app()).get("/users").status_code == 404


def test_no_warning_for_valid_routes(project):
    (project / "routes" / "ok.py").write_text("async def get():\n    return {}\n")
    (project / "routes" / "ws.py").write_text("async def websocket(ws):\n    pass\n")
    assert create_runapi_app().route_warnings == []


def test_imported_names_are_not_suggested(project):
    (project / "routes" / "x.py").write_text("from os.path import join as get_path\n")
    app = create_runapi_app()
    assert "Did you mean" not in app.route_warnings[0]


def test_log_requests_follows_debug_but_can_be_overridden(monkeypatch):
    monkeypatch.delenv("LOG_REQUESTS", raising=False)
    monkeypatch.setenv("DEBUG", "true")
    assert RunApiConfig().log_requests is True
    monkeypatch.setenv("DEBUG", "false")
    assert RunApiConfig().log_requests is False
    monkeypatch.setenv("LOG_REQUESTS", "true")
    assert RunApiConfig().log_requests is True


def test_request_logging_can_be_disabled(project, monkeypatch, caplog):
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_REQUESTS", "false")
    load_config()
    (project / "routes" / "ok.py").write_text("async def get():\n    return {}\n")
    client = TestClient(create_runapi_app().get_app())
    with caplog.at_level("INFO", logger="runapi"):
        client.get("/ok")
    assert not [r for r in caplog.records if r.getMessage().startswith("Request:")]


@pytest.mark.parametrize(
    "url, expect_error, expect_warning",
    [
        ("sqlite+aiosqlite:///./app.db", False, False),
        ("postgresql+asyncpg://u:p@localhost/db", False, False),
        ("localhost/mydb", True, False),
        ("postgres://u:p@localhost/db", False, True),
        ("postgresql://u:p@localhost/db", False, True),
        ("sqlite:///./app.db", False, True),
    ],
)
def test_database_url_validation(monkeypatch, url, expect_error, expect_warning):
    monkeypatch.setenv("SECRET_KEY", SECRET)
    monkeypatch.setenv("DATABASE_URL", url)
    result = RunApiConfig().validate_settings()
    assert bool([e for e in result["errors"] if "DATABASE_URL" in e]) is expect_error
    assert bool([w for w in result["warnings"] if "DATABASE_URL" in w]) is expect_warning
    if expect_error or expect_warning:
        text = " ".join(result["errors"] + result["warnings"])
        assert "asyncpg" in text or "aiosqlite" in text or "dialect://" in text
