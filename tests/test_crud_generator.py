import sys

import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from runapi import create_runapi_app
from runapi.cli import app
from runapi.config import load_config

runner = CliRunner()


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert runner.invoke(app, ["init", "demo"]).exit_code == 0
    monkeypatch.chdir(tmp_path / "demo")
    monkeypatch.syspath_prepend(str(tmp_path / "demo"))
    for name in [
        m
        for m in sys.modules
        if m.split(".")[0] in {"routes", "schemas", "services", "repositories"}
    ]:
        del sys.modules[name]
    return tmp_path / "demo"


def test_crud_roundtrip(project):
    result = runner.invoke(app, ["generate", "crud", "widget"])
    assert result.exit_code == 0, result.output
    load_config()
    client = TestClient(create_runapi_app().get_app())

    assert client.get("/widget").json()["items"] == []

    created = client.post("/widget", json={"name": "gear"})
    assert created.status_code == 201
    item = created.json()
    assert item["name"] == "gear" and "id" in item

    assert client.get(f"/widget/{item['id']}").json()["name"] == "gear"
    assert client.get("/widget").json()["total"] == 1

    updated = client.put(f"/widget/{item['id']}", json={"name": "cog"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "cog"

    assert client.delete(f"/widget/{item['id']}").status_code == 204
    assert client.get(f"/widget/{item['id']}").status_code == 404


def test_crud_validates_body(project):
    runner.invoke(app, ["generate", "crud", "widget"])
    load_config()
    client = TestClient(create_runapi_app().get_app())
    assert client.post("/widget", json={}).status_code == 422


def test_crud_refuses_to_overwrite(project):
    assert runner.invoke(app, ["generate", "crud", "widget"]).exit_code == 0
    again = runner.invoke(app, ["generate", "crud", "widget"])
    assert again.exit_code == 1
    assert "Refusing to overwrite" in again.output


def test_crud_rejects_bad_name(project):
    assert runner.invoke(app, ["generate", "crud", "../evil"]).exit_code == 1
