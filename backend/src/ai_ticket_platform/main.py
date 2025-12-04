from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from ai_ticket_platform.core.clients.firebase import initialize_firebase
from ai_ticket_platform.core.logger.logger import initialize_logger
import ai_ticket_platform.core.clients as clients
import ai_ticket_platform.core.settings as settings
from ai_ticket_platform.services.caching import CacheManager
from ai_ticket_platform.routers import (
	health_router,
    slack_router,
    documents_router,
    external_router,
    tickets_router,
    intents_router,
    articles_router,
)

# Removed: drafts, publishing, widget routers - not needed with frontend's Article model
import logging
from prometheus_fastapi_instrumentator import Instrumentator


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Context manager to handle application startup and shutdown events.
    This is the recommended way to manage resources that need to be
    available for the entire application lifecycle.
    """
    # initialize_firebase()
    initialize_logger()
    settings.app_settings = settings.initialize_settings()
    # clients.s3_client = clients.initialize_aws_s3_client()
    # clients.secrets_manager_client = clients.initialize_aws_secrets_manager_client()
    clients.redis = clients.initialize_redis_client()

    # Initialize Redis client and cache manager
    redis_instance = await clients.redis.get_client()
    clients.cache_manager = CacheManager(redis_instance)
    logger.info("Initializing ChromaDB for RAG")
    clients.chroma_vectorstore = clients.initialize_chroma_vectorstore(settings.app_settings)

    yield

    # --- Shutdown ---
    # You can add any cleanup code here, like closing database connections.
    logger.debug("INFO:     Application shutdown complete.")


app = FastAPI(title="AI Ticket Platform", lifespan=lifespan)

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_methods=["*"],
	allow_headers=["*"],
	allow_credentials=True,
)

# Include routers - frontend + caching
routers = [
	health_router,
	slack_router,
	documents_router,
	tickets_router,
	external_router,
	intents_router,
	articles_router,
]

# Serve widget folder
widget_dir = Path(__file__).parent / "widget"
app.mount("/widget", StaticFiles(directory=str(widget_dir)), name="widget")

for router in routers:
	app.include_router(router, prefix="/api")

Instrumentator().instrument(app).expose(app)
