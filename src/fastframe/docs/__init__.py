"""Optional OpenAPI docs.

Listing ``"fastframe.docs"`` in ``INSTALLED_APPS`` turns on FastAPI's
schema, Swagger UI, and ReDoc. Leave it out and none of those routes
exist. This is not a second docs system.
"""

from fastframe.docs.apps import DocsConfig

__all__ = ["DocsConfig"]
