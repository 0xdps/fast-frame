"""Audit log for admin/API mutations.

Every create, update, and delete made through the admin API
(:func:`fastframe.admin.api.get_admin_api_router`) or the token-authenticated
REST API (:func:`fastframe.api.get_rest_api_router`) is recorded here — both
surfaces share the same ``_build_crud_router`` implementation, so this is
the single place that instruments them.

``AuditLog`` is registered with :data:`fastframe.admin.site.admin_site`
automatically (importing this module has that side effect — see
:func:`fastframe.admin.include_admin`), so it shows up in the admin UI as a
read-only resource. It's a plain model like any other, so it's reachable
through ``AuditLog.objects`` too.
"""

from __future__ import annotations

from typing import Any

from fastframe.admin.site import ModelAdmin, admin_site
from fastframe.models import Model, fields


class AuditLog(Model):
    """One row per create/update/delete made through admin or the REST API."""

    user_id = fields.CharField(
        max_length=64,
        null=True,
        blank=True,
        help_text="String form of the acting user's primary key (survives PK type changes).",
    )
    username = fields.CharField(max_length=150, blank=True, default="")
    action = fields.CharField(
        max_length=10,
        choices=[("create", "Create"), ("update", "Update"), ("delete", "Delete")],
    )
    source = fields.CharField(
        max_length=10,
        choices=[("admin", "Admin UI"), ("api", "REST API")],
        default="admin",
    )
    model_name = fields.CharField(max_length=100)
    object_id = fields.CharField(max_length=64, blank=True, default="")
    object_repr = fields.CharField(max_length=255, blank=True, default="")
    changes = fields.JSONField(
        default=dict,
        help_text=("create/delete: {'fields': {...}} snapshot. update: {field: {'old': ..., 'new': ...}} diff."),
    )
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "admin_audit_log"
        ordering = ["-created_at"]
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log"
        app_label = "admin"

    def __str__(self) -> str:
        who = self.username or "system"
        return f"{self.action} {self.model_name}#{self.object_id} by {who}"


class AuditLogAdmin(ModelAdmin):
    """Read-only in the admin — audit entries are never editable."""

    list_display = ["created_at", "username", "action", "model_name", "object_repr", "source"]
    list_filter = ["action", "model_name", "source"]
    search_fields = ["username", "model_name", "object_repr"]
    ordering = ["-created_at"]

    has_add_permission = False
    has_change_permission = False
    has_delete_permission = False
    show_in_navigation = False


admin_site.register(AuditLog, AuditLogAdmin)


def record_audit(
    session: Any,
    *,
    user: Any,
    action: str,
    model_name: str,
    object_id: str,
    object_repr: str,
    changes: dict[str, Any] | None,
    source: str,
) -> None:
    """Write one ``AuditLog`` row. Best-effort — never raises into the caller.

    Args:
        session: The active SQLAlchemy session (same one the mutation used —
            the entry is flushed as part of the same transaction).
        user: The authenticated user snapshot (has ``.id``/``.username``),
            or ``None`` for system actions.
        action: ``"create"``, ``"update"``, or ``"delete"``.
        model_name: The mutated model's class name.
        object_id: String form of the affected record's primary key.
        object_repr: ``str()`` of the affected record (captured before
            deletion, for deletes).
        changes: Structured diff/snapshot — see :class:`AuditLog.changes`.
        source: ``"admin"`` or ``"api"``.
    """
    try:
        from fastframe.admin.serializers import serialize_value

        entry = AuditLog(
            user_id=serialize_value(getattr(user, "id", None)) if user is not None else None,
            username=getattr(user, "username", "") or "" if user is not None else "",
            action=action,
            source=source,
            model_name=model_name,
            object_id=object_id,
            object_repr=object_repr,
            changes=changes or {},
        )
        session.add(entry)
        session.flush()
    except Exception:  # noqa: BLE001 - audit logging must never break a request
        pass


__all__ = ["AuditLog", "AuditLogAdmin", "record_audit"]
