import os

os.environ.setdefault("FASTFRAME_SETTINGS_MODULE", "config.settings")

from fastframe.http.asgi import get_asgi_application

application = get_asgi_application()
