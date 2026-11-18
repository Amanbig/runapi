import pytest
from fastapi.testclient import TestClient

from runapi import ConfigurationError, RouteLoadError, create_runapi_app
from runapi.config import RunApiConfig

GOOD_SECRET = "a-very-long-random-secret-key-for-tests-0123456789"


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    for key in ["ENVIRONMENT", "DEBUG", "CORS_ORIGINS", "CORS_CREDENTIALS", "STRICT_ROUTES"]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("SECRET_KEY", GOOD_SECRET)
    return monkeypatch


def _route(root, name, body):
    (root / "routes").mkdir(exist_ok=True)
    (root / "routes" / name).write_text(body, encoding="utf-8")


def test_defaults_are_safe(env):
    cfg = RunApiConfig()
    assert cfg.environment == "development"
    assert cfg.debug is True
    assert cfg.cors_credentials is False
    assert cfg.validate()["errors"] == []


def test_production_defaults(env):
    env.setenv("ENVIRONMENT", "production")
    cfg = RunApiConfig()
    assert cfg.debug is False
    assert cfg.strict_routes is True
    assert cfg.is_production()


def test_validate_flags_problems(env):
    env.setenv("SECRET_KEY", "dev-secret-key-change-in-production")
    env.setenv("CORS_ORIGINS", "*")
    env.setenv("CORS_CREDENTIALS", "true")
    errors = RunApiConfig().validate()["errors"]
    assert any("SECRET_KEY" in e for e in errors)
    assert any("CORS" in e for e in errors)


def test_env_file_does_not_override_real_env(env, tmp_path):
    (tmp_path / ".env").write_text("PORT=1234\nHOST=1.2.3.4\n")
    env.setenv("PORT", "9999")
    env.delenv("HOST", raising=False)
    cfg = RunApiConfig()
    assert cfg.port == 9999
    assert cfg.host == "1.2.3.4"
    env.delenv("HOST", raising=False)


def test_production_refuses_unsafe_config(env):
    env.setenv("ENVIRONMENT", "production")
    env.setenv("DEBUG", "true")
    from runapi.config import load_config

    load_config()
    with pytest.raises(ConfigurationError):
        create_runapi_app()
    env.delenv("ENVIRONMENT")
    env.delenv("DEBUG")
    load_config()


def test_broken_route_dev_mode_logs_and_continues(env, tmp_path):
    from runapi.config import load_config

    load_config()
    _route(tmp_path, "ok.py", "async def get():\n    return {'ok': 1}\n")
    _route(tmp_path, "broken.py", "import does_not_exist\n")
    app = create_runapi_app()
    assert len(app.route_errors) == 1
    assert TestClient(app.get_app()).get("/ok").status_code == 200


def test_broken_route_strict_mode_fails(env, tmp_path):
    env.setenv("STRICT_ROUTES", "true")
    from runapi.config import load_config

    load_config()
    _route(tmp_path, "broken.py", "import does_not_exist\n")
    with pytest.raises(RouteLoadError):
        create_runapi_app()
    env.delenv("STRICT_ROUTES")
    load_config()


def test_health_and_ready(env):
    from runapi.config import load_config

    load_config()
    app = create_runapi_app()
    state = {"ok": True}
    app.add_readiness_check("db", lambda: state["ok"])
    client = TestClient(app.get_app())
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").status_code == 200
    state["ok"] = False
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["checks"] == {"db": False}


def test_user_health_route_not_overridden(env, tmp_path):
    from runapi.config import load_config

    load_config()
    _route(tmp_path, "health.py", "async def get():\n    return {'custom': True}\n")
    assert TestClient(create_runapi_app().get_app()).get("/health").json() == {"custom": True}


def test_lifespan_hooks_run_in_order(env):
    from runapi.config import load_config

    load_config()
    app = create_runapi_app()
    calls = []
    app.on_startup(lambda: calls.append("start1"))

    @app.on_startup
    async def start2():
        calls.append("start2")

    app.on_shutdown(lambda: calls.append("stop1"))
    app.on_shutdown(lambda: calls.append("stop2"))
    with TestClient(app.get_app()):
        assert calls == ["start1", "start2"]
    assert calls == ["start1", "start2", "stop2", "stop1"]
