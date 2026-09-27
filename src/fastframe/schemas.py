"""Curated schema imports. Pydantic owns the behavior.

These names are the supported entry point for request and response
models. They are the Pydantic classes, not a subclass and not a second
validator. Import from ``pydantic`` when you need something that is not
listed here.
"""

from pydantic import BaseModel, Field

__all__ = ["BaseModel", "Field"]
