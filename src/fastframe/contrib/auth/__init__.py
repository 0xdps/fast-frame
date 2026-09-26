"""FastFrame authentication system."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastframe.models import Model


def get_user_model() -> type[Model]:
    """
    Return the User model that is active in this project.
    
    Similar to Django's get_user_model(), this allows apps to reference
    the user model without hard-coding a specific model class.
    
    Returns:
        The user model class specified by AUTH_USER_MODEL setting
    """
    from fastframe.conf import settings
    
    app_label, model_name = settings.AUTH_USER_MODEL.split('.')
    
    # Import the module containing the model
    try:
        if app_label == 'auth':
            # Default built-in User model
            from .models import User
            return User
        else:
            # Custom user model in another app
            module = importlib.import_module(f"{app_label}.models")
            return getattr(module, model_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Could not import user model '{settings.AUTH_USER_MODEL}': {e}"
        ) from e


def authenticate(username: str, password: str) -> Model | None:
    """
    Verify credentials against the active user model.

    Similar to Django's authenticate(). Looks up the user by username,
    checks the password hash, and rejects inactive users.

    Args:
        username: The username to look up.
        password: The plaintext password to verify.

    Returns:
        The authenticated user instance, or None if credentials are invalid.
    """
    from fastframe.models.exceptions import DoesNotExist, MultipleObjectsReturned

    if not username or not password:
        return None

    user_model = get_user_model()
    try:
        user = user_model.objects.get(username=username)
    except (DoesNotExist, MultipleObjectsReturned):
        return None

    if not getattr(user, "is_active", True):
        return None
    if not user.check_password(password):
        return None
    return user