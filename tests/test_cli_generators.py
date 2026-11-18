import ast

import pytest
from typer.testing import CliRunner

from runapi.cli import app

runner = CliRunner()


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("SECRET_KEY", "a-very-long-random-secret-key-for-tests-0123456789")
    result = runner.invoke(app, ["init", "demo"])
    assert result.exit_code == 0
    monkeypatch.chdir(tmp_path / "demo")
    return tmp_path / "demo"


def _generated_files(root):
    return {p for p in root.rglob("*.py") if p.name != "__init__.py"}


@pytest.mark.parametrize("item", ["route", "schema", "repository", "service"])
def test_generators_produce_valid_python(project, item):
    before = _generated_files(project)
    result = runner.invoke(app, ["generate", item, "widget"])
    assert result.exit_code == 0, result.output
    new = _generated_files(project) - before
    assert new, f"{item} generator created no file"
    for path in new:
        ast.parse(path.read_text(encoding="utf-8"))  # must be syntactically valid


def test_generate_middleware(project):
    result = runner.invoke(app, ["generate", "middleware", "audit"])
    assert result.exit_code == 0, result.output


def test_generate_unknown_item(project):
    result = runner.invoke(app, ["generate", "bogus", "x"])
    assert result.exit_code == 1
    assert "Unknown generator" in result.output


def test_routes_and_schemas_and_info(project):
    runner.invoke(app, ["generate", "schema", "widget"])
    routes = runner.invoke(app, ["routes"])
    assert routes.exit_code == 0
    assert "/api/hello" in routes.output
    assert runner.invoke(app, ["schemas"]).exit_code == 0
    info = runner.invoke(app, ["info"])
    assert info.exit_code == 0
    assert "main.py" in info.output


def test_routes_without_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["routes"])
    assert result.exit_code == 1


def test_init_refuses_existing_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "exists").mkdir()
    assert runner.invoke(app, ["init", "exists"]).exit_code == 1


def test_dev_requires_main(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["dev"])
    assert result.exit_code == 1
    assert "main.py not found" in result.output


def test_doctor_passes_on_fresh_project(project):
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.output
