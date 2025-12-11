import logging
from typing import Any, Dict, List, Optional

from ai_ticket_platform.core.settings.app_settings import initialize_settings
from ai_ticket_platform.database.main import initialize_db_engine
from ai_ticket_platform.core.clients.chroma_client import get_chroma_vectorstore
from ai_ticket_platform.services.content_generation.article_service import (
	ArticleGenerationService,
)
from ai_ticket_platform.services.queue_manager.async_helper import _run_async

logger = logging.getLogger(__name__)


def generate_article_task(
	intent_id: int,
	feedback: Optional[str] = None,
	previous_article_id: Optional[int] = None,
) -> Dict[str, Any]:
	"""
	RQ Task: Generate or iterate article for an intent.

	This single task handles both initial generation and iteration:
	- If feedback is None: Initial generation
	- If feedback is provided: Iteration with feedback

	Args:
	    intent_id: Intent ID
	    feedback: Optional human feedback for iteration
	    previous_article_id: Optional previous article ID for iteration

	Returns:
	    Dict with generation result
	"""
	is_iteration = feedback is not None
	action = "Iterating" if is_iteration else "Generating"

	logger.info(f"[QUEUE TASK] {action} article for intent {intent_id}")

	try:
		settings = initialize_settings()
		AsyncSessionLocal = initialize_db_engine()

		# Initialize ChromaDB for this worker
		get_chroma_vectorstore(settings)

		async def generate():
			async with AsyncSessionLocal() as db:
				service = ArticleGenerationService(settings)
				result = await service.generate_article(
					intent_id=intent_id,
					db=db,
					feedback=feedback,
					previous_article_id=previous_article_id,
				)
				return result

		result = _run_async(generate())

		# Check if result indicates error
		if result.get("status") == "error":
			error_msg = result.get("error", "Unknown error")
			logger.error(
				f"[QUEUE TASK] {action} article for intent {intent_id} failed: {error_msg}"
			)
			raise RuntimeError(f"Article generation failed: {error_msg}")

		logger.info(f"[QUEUE TASK] {action} article for intent {intent_id}: success")
		return result

	except Exception as e:
		logger.error(
			f"[QUEUE TASK] Error {action.lower()} article for intent {intent_id}: {e}"
		)
		raise
