"""AppConfig for FastAPI's built-in OpenAPI docs.

Listing ``"fastframe.docs"`` in ``INSTALLED_APPS`` is what turns Swagger
on. There is no ``ENABLE_OPENAPI`` setting. See docs/settings.md.
"""

from __future__ import annotations

from fastframe.core.apps import AppConfig


class DocsConfig(AppConfig):
    name = "fastframe.docs"
    label = "docs"

    def ready(self) -> None:
        # The factory reads this app's presence and passes docs_url to
        # FastAPI(). Routes are not built here.
        return None
