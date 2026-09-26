"""Django-style permission strings, resolved from a user's own grants plus
their :class:`~fastframe.contrib.auth.models.Group` memberships.

There's no dedicated ``Permission`` table — a permission is just a string
of the form ``"{app_label}.{action}_{model_name}"`` (e.g.
``"blog.change_post"``), matching Django's convention closely enough to be
familiar, without the extra ``ContentType``/``Permission`` model machinery.

Enforcement is opt-in per model: :class:`fastframe.admin.site.ModelAdmin`
only consults these when ``enforce_permissions = True`` is set on the
admin class — by default, every model behaves exactly as it did before
this module existed (static ``has_*_permission`` booleans, same for every
user). See :mod:`fastframe.admin.site` and ``docs/permissions.md``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastframe.models import Model

#: The four Django-style actions a ModelAdmin can gate.
PERMISSION_ACTIONS = ("view", "add", "change", "delete")


def permission_codename(model: type[Model], action: str) -> str:
    """Build the permission string for ``action`` on ``model``.

    Example: ``permission_codename(Post, "change") == "blog.change_post"``.
    """
    app_label = model._meta.get("app_label", "app")
    return f"{app_label}.{action}_{model.__name__.lower()}"


def get_effective_permissions(user: Any) -> frozenset[str]:
    """Flatten a user's own ``permissions`` plus every group's ``permissions``.

    Works against a *live* ORM instance (needs to walk ``user.groups``);
    call this while the user is still attached to a session, then embed
    the result in any snapshot you hand out afterwards.
    """
    own = set(getattr(user, "permissions", None) or [])
    groups = getattr(user, "groups", None)
    if groups is not None:
        try:
            for group in groups.all():
                own.update(group.permissions or [])
        except Exception:  # noqa: BLE001 - defensive; a bad relationship shouldn't 403 everything
            pass
    return frozenset(own)


def user_has_perm(user: Any, perm: str) -> bool:
    """Check a single permission string against a user (or user snapshot).

    Superusers (``is_superuser``) always pass. Works against either a
    live ``User`` instance (flattens ``.groups`` on the fly) or a snapshot
    whose ``.permissions`` is already the flattened set (see
    :func:`get_effective_permissions` — snapshots have no ``.groups``
    attribute, so this just reads the precomputed set back).
    """
    if user is None:
        return False
    if bool(getattr(user, "is_superuser", False)):
        return True
    return perm in get_effective_permissions(user)


def user_has_model_perm(user: Any, model: type[Model], action: str) -> bool:
    """Check ``"{app_label}.{action}_{model}"`` against a user (or snapshot)."""
    return user_has_perm(user, permission_codename(model, action))


__all__ = [
    "PERMISSION_ACTIONS",
    "permission_codename",
    "get_effective_permissions",
    "user_has_perm",
    "user_has_model_perm",
]
