#!/usr/bin/env python
"""Admin bound to accounts.CustomUser via AUTH_USER_MODEL."""

import os

os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.core.app import create_app
from fastframe.db.engine import get_engine
from fastframe.models import Model

app = create_app()
Model.metadata.create_all(bind=get_engine())
