import pytest

from runapi import auth


@pytest.fixture
def manager(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-revocation-tests-0123456789")
    from runapi.config import load_config

    load_config()
    return auth.JWTManager(secret_key="test-secret-key-for-revocation-tests-0123456789")


def test_revoked_token_rejected(manager):
    token = manager.create_access_token({"sub": "u1"})
    assert manager.verify_token(token)["sub"] == "u1"
    assert manager.revoke_token(token) is True
    assert manager.verify_token(token) is None


def test_revoke_invalid_token(manager):
    assert manager.revoke_token("not-a-token") is False


def test_rotate_refresh_token(manager):
    refresh = manager.create_refresh_token({"sub": "u1"})
    pair = manager.rotate_refresh_token(refresh)
    assert pair is not None
    assert manager.verify_token(pair["access_token"])["sub"] == "u1"
    # old refresh token can no longer be used
    assert manager.rotate_refresh_token(refresh) is None
    assert manager.verify_token(pair["refresh_token"])["type"] == "refresh"


def test_rotate_rejects_access_token(manager):
    assert manager.rotate_refresh_token(manager.create_access_token({"sub": "u1"})) is None
