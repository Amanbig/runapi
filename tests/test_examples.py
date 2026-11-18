from pathlib import Path

from fastapi.testclient import TestClient

from runapi import create_runapi_app
from runapi.config import load_config

EXAMPLE = Path(__file__).parent.parent / "examples" / "basic"


def test_basic_example(monkeypatch):
    monkeypatch.chdir(EXAMPLE)
    monkeypatch.setenv("SECRET_KEY", "example-test-secret-key-0123456789abcdef")
    monkeypatch.syspath_prepend(str(EXAMPLE))
    load_config()
    client = TestClient(create_runapi_app().get_app())
    assert client.get("/").json()["message"] == "Welcome to RunApi"
    assert client.get("/health").json() == {"status": "ok"}
    assert len(client.get("/api/users").json()) == 2
    assert client.get("/api/users/1").json()["name"] == "Ada"
    assert client.get("/api/users/99").status_code == 404
    with client.websocket_connect("/api/echo") as ws:
        ws.send_text("hi")
        assert ws.receive_text() == "hi"
