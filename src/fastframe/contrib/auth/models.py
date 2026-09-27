"""Default User model for FastFrame authentication."""

from __future__ import annotations

from typing import Any

from fastframe.models import Model, fields

from .hashers import check_password, make_password
from .validators import validate_password_strength


class User(Model):
    """Default user model with UUID v7 primary key and flexible metadata.
    
    This model can be used directly or extended. Override by setting
    AUTH_USER_MODEL in your settings to point to a custom user model.
    
    Uses metadata JSON field instead of separate is_staff/is_superuser
    flags for maximum flexibility in permissions and preferences.
    """
    
    # Primary key - auto-created based on DEFAULT_AUTO_FIELD setting
    # If using UUIDField, will be UUID v7 (time-ordered, database-optimized)
    
    # Identity fields
    username = fields.CharField(
        max_length=150, 
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
    )
    email = fields.EmailField(
        unique=True,
        help_text="User's email address"
    )
    first_name = fields.CharField(
        max_length=150, 
        blank=True, 
        default="",
        help_text="User's first name"
    )
    last_name = fields.CharField(
        max_length=150, 
        blank=True, 
        default="",
        help_text="User's last name"
    )
    
    # Authentication
    password = fields.CharField(
        max_length=255, 
        write_only=True,
        help_text="Password (hashed with PBKDF2)"
    )
    
    # Status
    is_active = fields.BooleanField(
        default=True,
        help_text="Designates whether this user should be treated as active"
    )
    
    # Flexible user_data for permissions, preferences, etc.
    # Note: Can't use 'metadata' as it conflicts with SQLAlchemy's metadata attribute
    user_data = fields.JSONField(
        default=dict,
        help_text="Flexible storage for permissions, preferences, admin access, etc."
    )

    # Group membership — each Group carries its own list of permission
    # strings; a user's effective permissions are their own plus every
    # group they belong to (see fastframe.contrib.auth.permissions).
    groups = fields.ManyToManyField("Group", related_name="users")

    # Timestamps (auto-populated)
    date_joined = fields.DateTimeField(
        auto_now_add=True,
        help_text="Date and time when the user account was created"
    )
    last_login = fields.DateTimeField(
        null=True, 
        blank=True,
        help_text="Date and time of last login"
    )
    
    class Meta:
        db_table = "auth_users"
        ordering = ["-date_joined"]  # Newest first (works great with UUID v7)
        verbose_name = "User"
        verbose_name_plural = "Users"
        app_label = "auth"
    
    def __str__(self) -> str:
        """String representation of user."""
        return str(self.username)
    
    def __repr__(self) -> str:
        """Developer representation of user."""
        return f"<User: {self.username}>"
    
    # Properties for common user_data access
    
    @property
    def can_access_admin(self) -> bool:
        """Check if user can access admin panel."""
        return self.user_data.get("admin_access", False)
    
    @can_access_admin.setter
    def can_access_admin(self, value: bool) -> None:
        """Set admin access permission."""
        self.user_data["admin_access"] = bool(value)
    
    @property
    def is_superuser(self) -> bool:
        """Check if user has superuser privileges (all permissions)."""
        return self.user_data.get("superuser", False)
    
    @is_superuser.setter
    def is_superuser(self, value: bool) -> None:
        """Set superuser status."""
        self.user_data["superuser"] = bool(value)
    
    @property
    def session_version(self) -> int:
        """Monotonic counter embedded in every session token issued to this user.

        Bump it (via :meth:`invalidate_sessions`) to make every previously
        issued session cookie stop working immediately, without needing a
        server-side session table or touching any other user's sessions.
        """
        return int(self.user_data.get("session_version", 0))

    def invalidate_sessions(self) -> None:
        """Invalidate every session cookie issued to this user so far.

        Bearer API tokens (:mod:`fastframe.contrib.auth.tokens`) are
        unaffected — revoke those individually via ``DELETE /api/auth/token``.
        Caller is responsible for saving the instance afterwards.
        """
        self.user_data["session_version"] = self.session_version + 1

    @property
    def permissions(self) -> list[str]:
        """Get list of user permissions."""
        return self.user_data.get("permissions", [])
    
    @permissions.setter
    def permissions(self, value: list[str]) -> None:
        """Set user permissions."""
        self.user_data["permissions"] = list(value)
    
    @property
    def preferences(self) -> dict[str, Any]:
        """Get user preferences."""
        return self.user_data.get("preferences", {})
    
    @preferences.setter
    def preferences(self, value: dict[str, Any]) -> None:
        """Set user preferences."""
        self.user_data["preferences"] = dict(value)
    
    # Permission methods
    
    def has_permission(self, perm: str) -> bool:
        """Check if user has specific permission, own or via a group.

        Args:
            perm: Permission string (e.g., "blog.add_post")

        Returns:
            True if user has permission, False otherwise
        """
        from .permissions import user_has_perm

        return user_has_perm(self, perm)

    # Alias matching the permissions module / Django's naming.
    has_perm = has_permission
    
    def add_permission(self, perm: str) -> None:
        """Add a permission to the user."""
        perms = self.permissions
        if perm not in perms:
            perms.append(perm)
            self.permissions = perms
    
    def remove_permission(self, perm: str) -> None:
        """Remove a permission from the user."""
        perms = self.permissions
        if perm in perms:
            perms.remove(perm)
            self.permissions = perms
    
    # Authentication methods
    
    def set_password(self, raw_password: str, *, validate: bool = True) -> None:
        """Hash and set user's password.

        Args:
            raw_password: The plaintext password to hash and store.
            validate: Enforce ``PASSWORD_MIN_LENGTH`` (and that the password
                isn't just the username). Set ``False`` to bypass — e.g. for
                seeding fixtures/tests with intentionally weak passwords.

        Raises:
            fastframe.models.exceptions.ValidationError: If ``validate`` and
                the password doesn't meet the minimum policy.
        """
        if validate:
            validate_password_strength(raw_password, username=self.username)
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password: str) -> bool:
        """Verify a password against the user's stored password.
        
        Args:
            raw_password: The plaintext password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return check_password(raw_password, self.password)
    
    # Name methods
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self) -> str:
        """Get user's short name (first name)."""
        return self.first_name or self.username


class Group(Model):
    """A named collection of permission strings, assignable to many users.

    There's no separate ``Permission`` model — ``permissions`` is just a
    flat list of ``"{app_label}.{action}_{model}"`` strings (e.g.
    ``"blog.change_post"``). A user's effective permissions are their own
    (``User.permissions``) plus every group they belong to — see
    :mod:`fastframe.contrib.auth.permissions`.
    """

    name = fields.CharField(max_length=150, unique=True)
    permissions = fields.JSONField(
        default=list,
        help_text="List of permission strings, e.g. ['blog.add_post', 'blog.change_post'].",
    )

    class Meta:
        db_table = "auth_groups"
        ordering = ["name"]
        verbose_name = "Group"
        verbose_name_plural = "Groups"
        app_label = "auth"

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return f"<Group: {self.name}>"