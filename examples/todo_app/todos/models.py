"""Models for the todos app."""

from __future__ import annotations

from fastframe.models import Model, fields


class Todo(Model):
    """Todo item model."""

    title = fields.CharField(max_length=200)
    done = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "todos"
        ordering = ["-created_at"]
        verbose_name = "Todo Item"
        verbose_name_plural = "Todo Items"
