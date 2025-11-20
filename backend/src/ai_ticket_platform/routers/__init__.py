from .health import router as health_router
from .slack import router as slack_router
from .tickets import router as tickets_router

routers = [health_router, slack_router, tickets_router]
