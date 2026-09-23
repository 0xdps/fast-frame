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
        )