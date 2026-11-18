import json
import logging

import pytest
from fastapi.testclient import TestClient

from runapi import ConfigurationError, create_runapi_app, get_request_id
from runapi.config import RunApiConfig, load_config
from runapi.logging import JSONFormatter, request_id_var

SECRET = "a-very-long-random-secret-key-for-tests-0123456789"


@pytest.fixture(autouse=True)
def clean_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    keys = ["ENVIRONMENT", "DEBUG", "PORT", "CORS_ORIGINS", "LOG_JSON", "RATE_LIMIT_CALLS"]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SECRET_KEY", SECRET)
    yield
    for key in keys:  # tests may set invalid values; clear them before reloading
        monkeypatch.delenv(key, raising=False)
    load_config()


def test_csv_lists_and_types(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://a.com, https://b.com")
    monkeypatch.setenv("PORT", "9000")
    cfg = RunApiConfig()
    assert cfg.cors_origins == ["https://a.com", "https://b.com"]
    assert cfg.port == 9000


def test_invalid_values_raise_clear_error(monkeypatch):
    monkeypatch.setenv("PORT", "not-a-number")
    with pytest.raises(ConfigurationError, match="PORT"):
        RunApiConfig()
    monkeypatch.setenv("PORT", "8000")
    monkeypatch.setenv("RATE_LIMIT_CALLS", "0")
    with pytest.raises(ConfigurationError, match="RATE_LIMIT_CALLS"):
        RunApiConfig()


def test_json_logging_default_follows_environment(monkeypatch):
    assert RunApiConfig().log_json is False
    monkeypatch.setenv("ENVIRONMENT", "production")
    assert RunApiConfig().log_json is True


def test_json_formatter_includes_request_id_and_extras():
    record = logging.LogRecord("x", logging.INFO, __file__, 1, "hello %s", ("w",), None)
    record.status_code = 200
    token = request_id_var.set("abc123")
    try:
        data = json.loads(JSONFormatter().format(record))
    finally:
        request_id_var.reset(token)
    assert data["message"] == "hello w"
    assert data["request_id"] == "abc123"
    assert data["status_code"] == 200
    assert data["level"] == "INFO"


def test_request_id_header_roundtrip(tmp_path):
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "rid.py").write_text(
        "from runapi import get_request_id\n\nasync def get():\n    return {'id': get_request_id()}\n"
    )
    load_config()
    client = TestClient(create_runapi_app().get_app())

    generated = client.get("/rid")
    assert generated.headers["X-Request-ID"] == generated.json()["id"]
    assert len(generated.json()["id"]) == 32

    supplied = client.get("/rid", headers={"X-Request-ID": "my-trace-id"})
    assert supplied.headers["X-Request-ID"] == "my-trace-id"
    assert supplied.json()["id"] == "my-trace-id"
    assert get_request_id() is None
