#!/usr/bin/env python
"""Serve a project-local React admin from admin-ui/dist.

    python manage.py startadmin
    cd admin-ui && npm install && npm run build
    python -m uvicorn app:app --reload

Until `admin-ui/dist` exists, `/admin/` explains those steps. The API is
available either way.
"""

import os

os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.db.engine import get_engine
from fastframe.http.asgi import get_asgi_application
from fastframe.models import Model

app = get_asgi_application()
Model.metadata.create_all(bind=get_engine())
