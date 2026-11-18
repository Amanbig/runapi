import sys
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


def test_basic_crud_example(monkeypatch):
    example = Path(__file__).parent.parent / "examples" / "basic-crud"
    monkeypatch.chdir(example)
    monkeypatch.setenv("SECRET_KEY", "example-test-secret-key-0123456789abcdef")
    monkeypatch.syspath_prepend(str(example))
    for name in [
        m
        for m in sys.modules
        if m.split(".")[0] in {"routes", "schemas", "services", "repositories"}
    ]:
        del sys.modules[name]
    load_config()
    client = TestClient(create_runapi_app().get_app())

    assert client.get("/todos").json() == []
    created = client.post("/todos", json={"title": "write docs"})
    assert created.status_code == 201
    todo = created.json()
    assert todo["title"] == "write docs" and todo["done"] is False

    assert client.put(f"/todos/{todo['id']}", json={"done": True}).json()["done"] is True
    assert len(client.get("/todos", params={"done": True}).json()) == 1
    assert client.get("/todos", params={"done": False}).json() == []

    assert client.post("/todos", json={"title": ""}).status_code == 422
    assert client.post("/todos", json={"title": "todo"}).status_code == 400  # service rule
    assert client.get("/todos/999").status_code == 404

    assert client.delete(f"/todos/{todo['id']}").status_code == 204
    assert client.get(f"/todos/{todo['id']}").status_code == 404
