"""FastFrameAPI: explicit routes on top of a FastAPI ``APIRouter``.

Two styles, both backed by FastAPI:

- Function routes: ``@api.get("/users")``.
- Resource routes: ``@api.route("/users")`` on a class whose methods are
  named after HTTP verbs. The path is never inferred from the class name.

A native ``APIRouter`` remains a valid escape hatch. ``FastFrameAPI.router``
is that router, so it can be mounted beside one.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter
from fastapi.routing import APIRoute

from fastframe.http.responses import encode_response

EndpointDecorator = Callable[[Callable[..., Any]], Callable[..., Any]]

_HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options")


class FastFrameAPI:
    """A small routing facade over :class:`fastapi.APIRouter`.

    Keyword arguments are forwarded to the underlying router (``prefix``,
    ``tags``, ``dependencies``, …).
    """

    def __init__(self, **router_kwargs: Any) -> None:
        self.router = APIRouter(**router_kwargs)

    def get(self, path: str, **kwargs: Any) -> EndpointDecorator:
        return self._method("get", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> EndpointDecorator:
        return self._method("post", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> EndpointDecorator:
        return self._method("put", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> EndpointDecorator:
        return self._method("patch", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> EndpointDecorator:
        return self._method("delete", path, **kwargs)

    def head(self, path: str, **kwargs: Any) -> EndpointDecorator:
        return self._method("head", path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> EndpointDecorator:
        return self._method("options", path, **kwargs)

    def route(self, path: str, **kwargs: Any) -> Callable[[type], type]:
        """Register a resource class at an explicit path.

        Methods named ``get``, ``post``, ``put``, ``patch``, ``delete``,
        ``head``, or ``options`` become routes. Other methods are ignored.
        ``self`` is not a request parameter. Route kwargs (``tags``,
        ``response_model``, …) apply to every method on the class.
        """

        def decorator(cls: type) -> type:
            for method_name in _HTTP_METHODS:
                handler = getattr(cls, method_name, None)
                if handler is None or not callable(handler):
                    continue
                endpoint = _bind_resource_method(cls, handler)
                register = getattr(self.router, method_name)
                register(path, **kwargs)(endpoint)
            return cls

        return decorator

    def include_router(self, router: APIRouter, **kwargs: Any) -> None:
        """Mount a native FastAPI router. The escape hatch."""
        self.router.include_router(router, **kwargs)

    def _method(
        self, method: str, path: str, **kwargs: Any
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        register = getattr(self.router, method)

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            wrapped = _wrap_endpoint(func)
            return register(path, **kwargs)(wrapped)

        return decorator


def _wrap_endpoint(func: Callable[..., Any]) -> Callable[..., Any]:
    """Preserve the signature so FastAPI still sees path and body params."""

    if inspect.iscoroutinefunction(func):

        async def endpoint(*args: Any, **kwargs: Any) -> Any:
            return encode_response(await func(*args, **kwargs))

    else:

        def endpoint(*args: Any, **kwargs: Any) -> Any:
            return encode_response(func(*args, **kwargs))

    endpoint.__signature__ = inspect.signature(func)  # type: ignore[attr-defined]
    endpoint.__name__ = func.__name__
    endpoint.__doc__ = func.__doc__
    endpoint.__annotations__ = getattr(func, "__annotations__", {})
    endpoint.__wrapped__ = func  # type: ignore[attr-defined]
    return endpoint


def _bind_resource_method(cls: type, handler: Callable[..., Any]) -> Callable[..., Any]:
    """Turn an instance method into an endpoint that constructs ``cls``."""
    signature = inspect.signature(handler)
    parameters = [param for name, param in signature.parameters.items() if name != "self"]
    public = signature.replace(parameters=parameters)

    if inspect.iscoroutinefunction(handler):

        async def endpoint(*args: Any, **kwargs: Any) -> Any:
            return encode_response(await handler(cls(), *args, **kwargs))

    else:

        def endpoint(*args: Any, **kwargs: Any) -> Any:
            return encode_response(handler(cls(), *args, **kwargs))

    endpoint.__signature__ = public  # type: ignore[attr-defined]
    endpoint.__name__ = f"{cls.__name__}.{handler.__name__}"
    endpoint.__doc__ = handler.__doc__
    annotations = dict(getattr(handler, "__annotations__", {}))
    annotations.pop("self", None)
    endpoint.__annotations__ = annotations
    return endpoint


def iter_routes(api: FastFrameAPI) -> list[APIRoute]:
    """Return the FastAPI routes registered on ``api``. Test helper."""
    return [route for route in api.router.routes if isinstance(route, APIRoute)]
