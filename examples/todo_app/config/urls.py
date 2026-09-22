from health.urls import router as health_router
from todos.urls import router as todos_router

routers = [
    todos_router,
    health_router,
]
