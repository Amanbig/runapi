from typer.testing import CliRunner

from runapi import __version__
from runapi.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_init_docker_and_secret(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["init", "demo", "--docker"])
    assert result.exit_code == 0
    for name in ["Dockerfile", ".dockerignore", "requirements.txt", ".env"]:
        assert (tmp_path / "demo" / name).exists()
    env = (tmp_path / "demo" / ".env").read_text()
    assert "dev-secret-key-change-in-production" not in env


def test_build_requires_dockerfile(tmp_path):
    result = runner.invoke(app, ["build", str(tmp_path)])
    assert result.exit_code == 1


def test_db_commands_registered():
    result = runner.invoke(app, ["db", "--help"])
    assert result.exit_code == 0
    assert "migrate" in result.output


def test_start_refuses_unsafe_production_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)
    (tmp_path / "main.py").write_text("app = None\n")
    (tmp_path / ".env").write_text("DEBUG=true\nSECRET_KEY=dev-secret-key-change-in-production\n")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    result = runner.invoke(app, ["start"])
    assert result.exit_code == 1
    assert "unsafe production configuration" in result.output
    monkeypatch.delenv("ENVIRONMENT", raising=False)
