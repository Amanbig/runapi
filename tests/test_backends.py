import time

import fakeredis
import fakeredis.aioredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from runapi import (
    JWTManager,
    MemoryRateLimitBackend,
    RateLimitMiddleware,
    RedisRateLimitBackend,
    RedisTokenBlacklist,
)

SECRET = "a-very-long-random-secret-key-for-tests-0123456789"


def make_app(backend, calls=3, **kwargs):
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, calls=calls, period=60, backend=backend, **kwargs)

    @app.get("/")
    async def index():
        return {"ok": True}

    return TestClient(app)


@pytest.mark.parametrize("kind", ["memory", "redis"])
def test_rate_limit_blocks_after_limit(kind):
    if kind == "memory":
        backend = MemoryRateLimitBackend()
    else:
        backend = RedisRateLimitBackend(fakeredis.aioredis.FakeRedis())
    client = make_app(backend)
    codes = [client.get("/").status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    blocked = client.get("/")
    assert int(blocked.headers["Retry-After"]) >= 1


def test_rate_limit_headers():
    client = make_app(MemoryRateLimitBackend())
    resp = client.get("/")
    assert resp.headers["X-RateLimit-Limit"] == "3"
    assert resp.headers["X-RateLimit-Remaining"] == "2"


def test_redis_backends_share_state_across_instances():
    shared = fakeredis.FakeServer()
    a = make_app(RedisRateLimitBackend(fakeredis.aioredis.FakeRedis(server=shared)))
    b = make_app(RedisRateLimitBackend(fakeredis.aioredis.FakeRedis(server=shared)))
    assert [a.get("/").status_code for _ in range(3)] == [200, 200, 200]
    assert b.get("/").status_code == 429  # a different "worker" sees the same counter


def test_x_forwarded_for_ignored_unless_trusted():
    client = make_app(MemoryRateLimitBackend(), calls=1)
    assert client.get("/", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    # a spoofed header must not give a fresh bucket
    assert client.get("/", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 429

    trusting = make_app(MemoryRateLimitBackend(), calls=1, trust_proxy_headers=True)
    assert trusting.get("/", headers={"X-Forwarded-For": "1.1.1.1"}).status_code == 200
    assert trusting.get("/", headers={"X-Forwarded-For": "2.2.2.2"}).status_code == 200


def test_redis_rate_limit_fails_open():
    class Broken:
        async def incr(self, *a, **k):
            raise ConnectionError("down")

    client = make_app(RedisRateLimitBackend(Broken()), calls=1)
    assert [client.get("/").status_code for _ in range(3)] == [200, 200, 200]


def test_memory_backend_purges_expired_windows():
    import asyncio

    backend = MemoryRateLimitBackend()

    async def run():
        await backend.hit("old", 1)
        backend._windows["old"][1] -= 10
        backend._last_purge -= 10
        await backend.hit("new", 1)

    asyncio.run(run())
    assert "old" not in backend._windows


def test_redis_token_blacklist_with_jwt(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", SECRET)
    manager = JWTManager(secret_key=SECRET)
    server = fakeredis.FakeServer()
    manager.blacklist = RedisTokenBlacklist(fakeredis.FakeRedis(server=server))
    token = manager.create_access_token({"sub": "u1"})
    assert manager.verify_token(token)
    assert manager.revoke_token(token)
    assert manager.verify_token(token) is None

    # another process sharing Redis also rejects it
    other = JWTManager(secret_key=SECRET)
    other.blacklist = RedisTokenBlacklist(fakeredis.FakeRedis(server=server))
    assert other.verify_token(token) is None


def test_redis_blacklist_sets_ttl():
    client = fakeredis.FakeRedis()
    bl = RedisTokenBlacklist(client)
    bl.add("jti1", time.time() + 100)
    assert 0 < client.ttl("runapi:revoked:jti1") <= 101


def test_redis_blacklist_fails_closed():
    class Broken:
        def exists(self, *a):
            raise ConnectionError("down")

    assert RedisTokenBlacklist(Broken()).is_revoked("x") is True


def test_redis_backend_requires_url(monkeypatch):
    from runapi.backends import uses_redis
    from runapi.config import RunApiConfig

    monkeypatch.setenv("CACHE_BACKEND", "redis")
    monkeypatch.delenv("REDIS_URL", raising=False)
    with pytest.raises(ValueError, match="REDIS_URL"):
        uses_redis(RunApiConfig())
