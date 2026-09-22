from fastframe.http.asgi import get_asgi_application

__all__ = ["get_asgi_application"]

# NOTE: `Pagination`/`pagination` (fastframe.http.pagination) are deliberately
# *not* re-exported here. Re-exporting a name identical to its submodule
# (e.g. `from fastframe.http.pagination import pagination`) shadows the
# submodule on this package's own attribute table — the same footgun
# `fastframe.core.__init__` already has for `bootstrap` (see
# tests/test_checks.py for a worked example of the failure mode). Import
# directly: `from fastframe.http.pagination import Pagination, pagination`.
