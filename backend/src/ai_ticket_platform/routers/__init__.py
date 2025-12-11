from .health import router as health_router
from .slack import router as slack_router
from .documents import router as documents_router
from .tickets import router as tickets_router
from .external import router as external_router
from .intents import router as intents_router
from .articles import router as articles_router
from .s3_test import router as s3_test_router

routers = [
	health_router,
	slack_router,
	documents_router,
	external_router,
	tickets_router,
	intents_router,
	articles_router,
	s3_test_router,
]
# widget router removed - requires PublishedArticle model not yet implemented
