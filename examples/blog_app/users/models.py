"""User model."""

import hashlib
import secrets

from sqlalchemy.orm import validates

from fastframe.models import Model, ValidationError, fields


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2. Already-hashed values are returned unchanged."""
    if password.startswith("pbkdf2_sha256$"):
        return password
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


class SimpleUser(Model):
    """Account used by the admin. Password is stored hashed and never returned by the API."""

    id = fields.UUIDField(primary_key=True)
    first_name = fields.CharField(max_length=50)
    last_name = fields.CharField(max_length=50)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.EmailField(unique=True)
    password = fields.CharField(max_length=255, write_only=True)
    is_active = fields.BooleanField(default=True)
    preferences = fields.JSONField(default=dict)

    class Meta:
        db_table = "simple_users"
        ordering = ["username"]
        verbose_name = "User"
        verbose_name_plural = "Users"
        app_label = "users"

    @validates("password")
    def _hash_password(self, _key: str, value: str | None) -> str | None:
        if not value:
            return value
        return hash_password(value)

    def clean(self):
        if not self.username.replace("_", "").isalnum():
            raise ValidationError("Username must be alphanumeric")
