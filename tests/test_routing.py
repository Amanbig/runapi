"""Tests for advanced file-based routing: groups, catch-all, ordering, websockets."""

import sys

import pytest
from fastapi.testclient import TestClient

from runapi import create_runapi_app


def _write(root, rel, content):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-routing-tests-0123456789")
    for name in [m for m in sys.modules if m.startswith("routes")]:
        del sys.modules[name]
    return tmp_path


def _client():
    return TestClient(create_runapi_app().get_app())


def test_catch_all_route(project):
    _write(
        project,
        "routes/docs/[...slug].py",
        "async def get(slug: str):\n    return {'slug': slug}\n",
    )
    r = _client().get("/docs/a/b/c")
    assert r.status_code == 200
    assert r.json() == {"slug": "a/b/c"}


def test_dynamic_folder(project):
    _write(
        project,
        "routes/users/[id]/posts.py",
        "async def get(id: str):\n    return {'user': id}\n",
    )
    assert _client().get("/users/7/posts").json() == {"user": "7"}


def test_route_group_not_in_url(project):
    _write(project, "routes/(admin)/stats.py", "async def get():\n    return {'ok': True}\n")
    client = _client()
    assert client.get("/stats").status_code == 200
    assert client.get("/(admin)/stats").status_code == 404


def test_static_beats_dynamic_and_catch_all(project):
    _write(
        project, "routes/items/[id].py", "async def get(id: str):\n    return {'kind': 'dynamic'}\n"
    )
    _write(project, "routes/items/new.py", "async def get():\n    return {'kind': 'static'}\n")
    _write(
        project,
        "routes/items/[...rest].py",
        "async def get(rest: str):\n    return {'kind': 'catch'}\n",
    )
    client = _client()
    assert client.get("/items/new").json()["kind"] == "static"
    assert client.get("/items/42").json()["kind"] == "dynamic"
    assert client.get("/items/a/b").json()["kind"] == "catch"


def test_websocket_route(project):
    _write(
        project,
        "routes/ws.py",
        "from fastapi import WebSocket\n\n"
        "async def websocket(ws: WebSocket):\n"
        "    await ws.accept()\n"
        "    await ws.send_text('hello')\n"
        "    await ws.close()\n",
    )
    with _client().websocket_connect("/ws") as ws:
        assert ws.receive_text() == "hello"
