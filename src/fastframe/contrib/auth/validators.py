"""Minimal password strength validation, run from ``User.set_password()``.

Deliberately small — a length floor plus an identical-to-username check —
rather than trying to reproduce Django's full ``AUTH_PASSWORD_VALIDATORS``
pluggable pipeline. Extend or replace by overriding ``set_password()`` on a
custom user model if you need more (breach-database checks, entropy
scoring, etc.).
"""

from __future__ import annotations

from fastframe.models.exceptions import ValidationError


def validate_password_strength(raw_password: str, *, username: str | None = None) -> None:
    """Raise :class:`ValidationError` if ``raw_password`` fails the policy.

    Checks (in order):
        1. Non-empty.
        2. At least ``settings.PASSWORD_MIN_LENGTH`` characters (default 8).
        3. Not equal to ``username`` (case-insensitive) — the single most
           common weak-password pattern.
    """
    try:
        from fastframe.conf import settings

        min_length = int(getattr(settings, "PASSWORD_MIN_LENGTH", 8))
    except (ImportError, AttributeError, TypeError, ValueError):
        min_length = 8

    if not raw_password:
        raise ValidationError(errors={"password": "This field is required."})
    if len(raw_password) < min_length:
        raise ValidationError(
            errors={"password": f"Must be at least {min_length} characters long."}
        )
    if username and raw_password.lower() == username.lower():
        raise ValidationError(
            errors={"password": "Password can't be the same as the username."}
        )


__all__ = ["validate_password_strength"]
