"""Signed session tokens for admin authentication.

Uses HMAC-SHA256 over ``settings.SECRET_KEY`` to sign a small JSON payload
(user id + expiry). No extra dependencies (no itsdangerous/JWT) — this is a
minimal, dependency-free equivalent of Django's signed cookie sessions.

Format: ``<base64url(payload)>.<base64url(hmac_signature)>``
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

# 14 days, matches common "remember me" session lifetimes.
DEFAULT_MAX_AGE = 60 * 60 * 24 * 14


def _secret_key() -> bytes:
    from fastframe.conf import settings

    key = getattr(settings, "SECRET_KEY", "") or ""
    return str(key).encode()


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _b64decode(encoded: str) -> bytes:
    padded = encoded + "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(padded.encode())


def _sign(payload: str) -> str:
    signature = hmac.new(_secret_key(), payload.encode(), hashlib.sha256).digest()
    return _b64encode(signature)


def create_session_token(data: dict[str, Any], max_age: int = DEFAULT_MAX_AGE) -> str:
    """Create a signed, expiring session token embedding ``data``.

    Args:
        data: JSON-serializable payload to embed (e.g. ``{"user_id": 1}``).
        max_age: Seconds until the token expires.

    Returns:
        An opaque signed token string, safe to store in a cookie.
    """
    envelope = {"data": data, "exp": int(time.time()) + max_age}
    encoded = _b64encode(json.dumps(envelope, separators=(",", ":")).encode())
    return f"{encoded}.{_sign(encoded)}"


def verify_session_token(token: str | None) -> dict[str, Any] | None:
    """Verify a session token's signature and expiry.

    Args:
        token: The token string from a cookie/header.

    Returns:
        The embedded ``data`` dict if the token is valid and unexpired,
        otherwise ``None``.
    """
    if not token or "." not in token:
        return None

    encoded, _, signature = token.partition(".")
    if not hmac.compare_digest(signature, _sign(encoded)):
        return None

    try:
        envelope = json.loads(_b64decode(encoded))
    except (ValueError, UnicodeDecodeError):
        return None

    if not isinstance(envelope, dict) or envelope.get("exp", 0) < time.time():
        return None

    data = envelope.get("data")
    return data if isinstance(data, dict) else None


__all__ = ["create_session_token", "verify_session_token", "DEFAULT_MAX_AGE"]
