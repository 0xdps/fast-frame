"""Settings that disable OpenAPI and the admin (not installed)."""

INSTALLED_APPS = []
DATABASE_URL = "sqlite://"
ENABLE_OPENAPI = False
AUTH_USER_MODEL = "auth.User"
DEFAULT_AUTO_FIELD = "AutoField"
SECRET_KEY = "test"
DEBUG = True
