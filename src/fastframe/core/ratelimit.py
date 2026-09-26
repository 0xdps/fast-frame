"""A small in-memory rate limiter, used to blunt brute-forcing on the
login/token endpoints (``/api/admin/login``, ``/api/auth/login``,
``/api/auth/token``).

Single-process, in-memory only — state isn't shared across worker
processes or instances. That's an intentional, documented limitation (see
``docs/ADMIN_SECURITY_WARNING.md``): this is meant to blunt naive scripted
attacks against a single dev/small deployment, not to be a production-grade
distributed rate limiter. Swap in a Redis- or database-backed
:class:`RateLimiter` subclass for multi-process deployments.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request


class RateLimiter:
    """Sliding-window limiter: at most ``max_attempts`` per ``window_seconds``.

    Exceeding the limit starts a ``lockout_seconds`` cooldown during which
    every call to :meth:`hit` keeps returning "blocked", even after the
    original window has rolled off — a few more failed attempts right at
    the edge of the window don't quietly restart a fresh, shorter window.
    """

    def __init__(
        self, *, max_attempts: int, window_seconds: float, lockout_seconds: float
    ) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)
        self._locked_until: dict[str, float] = {}
        self._lock = Lock()

    def is_blocked(self, key: str) -> tuple[bool, float]:
        """Return ``(blocked, retry_after_seconds)`` for ``key`` without recording a hit."""
        now = time.monotonic()
        with self._lock:
            locked_until = self._locked_until.get(key)
            if locked_until is not None:
                if now < locked_until:
                    return True, locked_until - now
                del self._locked_until[key]
            return False, 0.0

    def hit(self, key: str) -> tuple[bool, float]:
        """Record an attempt for ``key``; return ``(blocked, retry_after_seconds)``.

        Call this once per failed attempt (successful logins should call
        :meth:`reset` instead, so a genuine user isn't punished for a few
        earlier typos).
        """
        now = time.monotonic()
        with self._lock:
            locked_until = self._locked_until.get(key)
            if locked_until is not None:
                if now < locked_until:
                    return True, locked_until - now
                del self._locked_until[key]

            window_start = now - self.window_seconds
            attempts = [t for t in self._attempts[key] if t >= window_start]
            attempts.append(now)
            self._attempts[key] = attempts

            if len(attempts) > self.max_attempts:
                self._locked_until[key] = now + self.lockout_seconds
                return True, self.lockout_seconds
            return False, 0.0

    def reset(self, key: str) -> None:
        """Clear any recorded attempts/lockout for ``key`` (call on success)."""
        with self._lock:
            self._attempts.pop(key, None)
            self._locked_until.pop(key, None)

    def clear(self) -> None:
        """Drop all recorded state for every key."""
        with self._lock:
            self._attempts.clear()
            self._locked_until.clear()


_limiters: dict[str, RateLimiter] = {}
_limiters_lock = Lock()


def get_login_rate_limiter() -> RateLimiter:
    """The shared limiter for login/token-obtain endpoints, built from settings.

    Built once per process (from whatever ``RATE_LIMIT_LOGIN_*`` settings
    are active at first use) and cached — call :func:`reset_rate_limiters`
    after changing those settings (mainly relevant in tests) to pick up
    new thresholds.
    """
    with _limiters_lock:
        limiter = _limiters.get("login")
        if limiter is None:
            from fastframe.conf import settings

            limiter = RateLimiter(
                max_attempts=int(getattr(settings, "RATE_LIMIT_LOGIN_MAX_ATTEMPTS", 5)),
                window_seconds=float(getattr(settings, "RATE_LIMIT_LOGIN_WINDOW_SECONDS", 60)),
                lockout_seconds=float(getattr(settings, "RATE_LIMIT_LOGIN_LOCKOUT_SECONDS", 300)),
            )
            _limiters["login"] = limiter
        return limiter


def reset_rate_limiters() -> None:
    """Drop every cached limiter (and its state). Mainly for tests."""
    with _limiters_lock:
        _limiters.clear()


def rate_limit_key(request_ip: str | None, identifier: str) -> str:
    """Build a limiter key from the client IP and a request-supplied identifier
    (e.g. the attempted username) — limits both "one IP hammering many
    usernames" and "many IPs hammering one username" without conflating them
    into a single, easily-shared bucket.
    """
    return f"{request_ip or 'unknown'}:{identifier.lower()}"


def enforce_login_rate_limit(request: Request, identifier: str) -> None:
    """Raise ``HTTPException(429)`` if this (IP, identifier) pair is currently
    blocked, and record this as one more attempt. Call at the very top of a
    login/token-obtain handler, before checking credentials, then call
    :func:`record_login_success` if credentials turn out to be valid.

    No-ops entirely when ``RATE_LIMIT_LOGIN_ENABLED`` is false.
    """
    from fastapi import HTTPException

    from fastframe.conf import settings

    if not bool(getattr(settings, "RATE_LIMIT_LOGIN_ENABLED", True)):
        return

    client_ip = request.client.host if request.client else None
    key = rate_limit_key(client_ip, identifier)
    blocked, retry_after = get_login_rate_limiter().hit(key)
    if blocked:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(int(retry_after) + 1)},
        )


def record_login_success(request: Request, identifier: str) -> None:
    """Clear rate-limit state for this (IP, identifier) pair after a
    successful login — don't let a couple of earlier typos count against a
    genuine user going forward. No-ops when rate limiting is disabled.
    """
    from fastframe.conf import settings

    if not bool(getattr(settings, "RATE_LIMIT_LOGIN_ENABLED", True)):
        return

    client_ip = request.client.host if request.client else None
    key = rate_limit_key(client_ip, identifier)
    get_login_rate_limiter().reset(key)


__all__ = [
    "RateLimiter",
    "get_login_rate_limiter",
    "reset_rate_limiters",
    "rate_limit_key",
    "enforce_login_rate_limit",
    "record_login_success",
]
