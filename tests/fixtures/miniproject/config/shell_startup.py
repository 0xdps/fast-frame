"""Example shell startup script for the miniproject fixture."""

from fastframe.health import get_health_router

health_router = get_health_router()

__all__ = ["health_router"]
