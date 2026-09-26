"""Tests for login/token-obtain rate limiting (fastframe.core.ratelimit)."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from fastframe.contrib.auth.models import User
from fastframe.contrib.auth.views import get_auth_router
from fastframe.core.ratelimit import RateLimiter, reset_rate_limiters
from fastframe.db.session import session_scope
from fastframe.models import Model


@pytest.fixture
def app(miniproject_env, monkeypatch):
    monkeypatch.setattr("fastframe.conf.settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS", 3)
    monkeypatch.setattr("fastframe.conf.settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS", 60)
    monkeypatch.setattr("fastframe.conf.settings.RATE_LIMIT_LOGIN_LOCKOUT_SECONDS", 60)
    reset_rate_limiters()

    from fastframe.db.engine import get_engine

    Model.metadata.create_all(bind=get_engine())

    fastapi_app = FastAPI()
    fastapi_app.include_router(get_auth_router())

    with session_scope():
        for user in list(User.objects.all()):
            user.delete()
        user = User(username="dana", email="dana@example.com", password="")
        user.set_password("correct-pass")
        user.save()

    return fastapi_app


@pytest.fixture
def client(app):
    return TestClient(app)


def test_repeated_failed_logins_get_blocked(client):
    for _ in range(3):
        resp = client.post(
            "/api/auth/login", json={"username": "dana", "password": "wrong-pass"}
        )
        assert resp.status_code == 401

    blocked = client.post(
        "/api/auth/login", json={"username": "dana", "password": "wrong-pass"}
    )
    assert blocked.status_code == 429
    assert "Retry-After" in blocked.headers


def test_correct_password_still_blocked_during_lockout(client):
    """Once locked out, even the *correct* password is blocked until the
    lockout window passes — this is a request-rate limit, not just a
    failed-attempt counter."""
    for _ in range(3):
        client.post("/api/auth/login", json={"username": "dana", "password": "wrong-pass"})

    resp = client.post("/api/auth/login", json={"username": "dana", "password": "correct-pass"})
    assert resp.status_code == 429


def test_successful_login_resets_the_counter(client):
    client.post("/api/auth/login", json={"username": "dana", "password": "wrong-pass"})
    client.post("/api/auth/login", json={"username": "dana", "password": "wrong-pass"})

    success = client.post(
        "/api/auth/login", json={"username": "dana", "password": "correct-pass"}
    )
    assert success.status_code == 200

    # The failed attempts before the successful login shouldn't count
    # against this user going forward.
    for _ in range(2):
        resp = client.post(
            "/api/auth/login", json={"username": "dana", "password": "wrong-pass"}
        )
        assert resp.status_code == 401


def test_different_usernames_have_independent_buckets(client):
    for _ in range(3):
        client.post("/api/auth/login", json={"username": "dana", "password": "wrong-pass"})

    # "dana" is now locked out, but a different username isn't affected.
    resp = client.post(
        "/api/auth/login", json={"username": "someone-else", "password": "wrong-pass"}
    )
    assert resp.status_code == 401  # not 429 — unrelated bucket


def test_rate_limiting_can_be_disabled(client, monkeypatch):
    monkeypatch.setattr("fastframe.conf.settings.RATE_LIMIT_LOGIN_ENABLED", False)
    reset_rate_limiters()

    for _ in range(10):
        resp = client.post(
            "/api/auth/login", json={"username": "dana", "password": "wrong-pass"}
        )
        assert resp.status_code == 401  # never 429


# ----------------------------------------------------------------------
# RateLimiter unit tests (no HTTP layer)
# ----------------------------------------------------------------------


def test_rate_limiter_blocks_after_max_attempts():
    limiter = RateLimiter(max_attempts=2, window_seconds=60, lockout_seconds=30)
    assert limiter.hit("k") == (False, 0.0)
    assert limiter.hit("k") == (False, 0.0)
    blocked, retry_after = limiter.hit("k")
    assert blocked is True
    assert retry_after > 0


def test_rate_limiter_reset_clears_state():
    limiter = RateLimiter(max_attempts=1, window_seconds=60, lockout_seconds=30)
    limiter.hit("k")
    blocked, _ = limiter.hit("k")
    assert blocked is True

    limiter.reset("k")
    blocked, _ = limiter.hit("k")
    assert blocked is False


def test_rate_limiter_keys_are_independent():
    limiter = RateLimiter(max_attempts=1, window_seconds=60, lockout_seconds=30)
    limiter.hit("a")
    blocked_a, _ = limiter.hit("a")
    blocked_b, _ = limiter.hit("b")
    assert blocked_a is True
    assert blocked_b is False
