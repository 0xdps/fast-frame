#!/usr/bin/env python
"""Compiled admin and API on one process.

Create an admin user, then run: python -m uvicorn app:app --reload
Open http://127.0.0.1:8000/admin/
"""

import os

os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.db.engine import get_engine
from fastframe.http.asgi import get_asgi_application
from fastframe.models import Model

app = get_asgi_application()
Model.metadata.create_all(bind=get_engine())
