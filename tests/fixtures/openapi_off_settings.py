"""Settings with OpenAPI and the admin left uninstalled."""

INSTALLED_APPS = []
DATABASE_URL = "sqlite://"
AUTH_USER_MODEL = "auth.User"
DEFAULT_AUTO_FIELD = "AutoField"
SECRET_KEY = "test"
DEBUG = True
