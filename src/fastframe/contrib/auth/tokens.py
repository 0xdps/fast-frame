"""Opaque API tokens for the token-authenticated REST API (:mod:`fastframe.api`).

Similar to Django REST Framework's ``TokenAuthentication``, but the raw key
is never stored — only its SHA-256 hash. The raw key is returned exactly
once, when the token is created; lost keys can't be recovered, only revoked
and replaced.

A user can hold multiple tokens (e.g. one per device/integration); revoke
one without affecting the others via ``DELETE /api/auth/token``.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from typing import Any

from fastframe.models import Model, fields


class Token(Model):
    """An API token belonging to a user. The raw key is never stored."""

    key_hash = fields.CharField(max_length=64, unique=True)
    user_id = fields.CharField(
        max_length=64,
        help_text="String form of the owning user's primary key.",
    )
    name = fields.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Optional label (e.g. 'mobile app', 'CI pipeline').",
    )
    created_at = fields.DateTimeField(auto_now_add=True)
    last_used_at = fields.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "auth_tokens"
        ordering = ["-created_at"]
        verbose_name = "API Token"
        verbose_name_plural = "API Tokens"
        app_label = "auth"

    def __str__(self) -> str:
        return self.name or f"token for user {self.user_id}"


def generate_raw_token() -> str:
    """A new random, unguessable token key (64 hex chars / 256 bits)."""
    return secrets.token_hex(32)


def hash_token(raw_token: str) -> str:
    """SHA-256 hex digest of a raw token, for storage/lookup."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def create_token(user: Any, *, name: str = "") -> str:
    """Create a new token for ``user`` and return the raw key (shown once).

    Args:
        user: The user model instance the token authenticates as.
        name: Optional label for the token.

    Returns:
        The raw token string. Store it now — only its hash is kept.
    """
    from fastframe.admin.serializers import get_pk_name, serialize_value

    raw = generate_raw_token()
    pk_name = get_pk_name(type(user))
    Token(
        key_hash=hash_token(raw),
        user_id=str(serialize_value(getattr(user, pk_name))),
        name=name,
    ).save()
    return raw


def get_user_from_token(raw_token: str) -> Any | None:
    """Resolve the active user for a raw token, or ``None`` if invalid.

    Updates ``last_used_at`` on success. Returns ``None`` (rather than
    raising) for any lookup failure — missing token, deleted user, or
    inactive user.
    """
    if not raw_token:
        return None

    from fastframe.contrib.auth import get_user_model
    from fastframe.models.exceptions import DoesNotExist, MultipleObjectsReturned

    key_hash = hash_token(raw_token)
    try:
        token = Token.objects.get(key_hash=key_hash)
    except (DoesNotExist, MultipleObjectsReturned):
        return None

    # hash_token() is already a fixed-size digest comparison via the DB
    # index; the extra compare_digest below guards against any future
    # lookup path that might compare raw strings directly.
    if not hmac.compare_digest(token.key_hash, key_hash):
        return None

    user_model = get_user_model()
    pk_name = _pk_name(user_model)
    try:
        user = user_model.objects.get(**{pk_name: _coerce_pk(user_model, token.user_id)})
    except (DoesNotExist, MultipleObjectsReturned):
        return None

    if not getattr(user, "is_active", True):
        return None

    token.last_used_at = _utcnow()
    token.save()
    return user


def revoke_token(raw_token: str) -> bool:
    """Delete the token matching ``raw_token``. Returns True if one was found."""
    from fastframe.models.exceptions import DoesNotExist, MultipleObjectsReturned

    try:
        token = Token.objects.get(key_hash=hash_token(raw_token))
    except (DoesNotExist, MultipleObjectsReturned):
        return False
    token.delete()
    return True


def _pk_name(model: type) -> str:
    from fastframe.admin.serializers import get_pk_name

    return get_pk_name(model)


def _coerce_pk(model: type, raw_value: str) -> Any:
    """Coerce a string-form PK back into the type the model's PK field expects."""
    from fastframe.admin.serializers import deserialize_value

    pk_name = _pk_name(model)
    pk_field = model._meta["fields"][pk_name]
    return deserialize_value(pk_field, raw_value)


def _utcnow():
    from datetime import UTC, datetime

    return datetime.now(UTC)


__all__ = [
    "Token",
    "generate_raw_token",
    "hash_token",
    "create_token",
    "get_user_from_token",
    "revoke_token",
]
