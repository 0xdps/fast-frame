#!/usr/bin/env python
"""Compiled admin and API on one process.

Create an admin user, then run: python -m uvicorn app:app --reload
Open http://127.0.0.1:8000/admin/
"""

import os

os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.core.app import create_app
from fastframe.db.engine import get_engine
from fastframe.models import Model

app = create_app()
Model.metadata.create_all(bind=get_engine())
