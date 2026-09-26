#!/usr/bin/env python
"""Admin bound to accounts.CustomUser via AUTH_USER_MODEL."""

import os

os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.db.engine import get_engine
from fastframe.http.asgi import get_asgi_application
from fastframe.models import Model

app = get_asgi_application()
Model.metadata.create_all(bind=get_engine())
