import logging
from typing import Any, Dict, List, Optional

from ai_ticket_platform.core.settings.app_settings import initialize_settings
from ai_ticket_platform.database.main import initialize_db_engine
from ai_ticket_platform.core.clients.chroma_client import get_chroma_vectorstore
from ai_ticket_platform.core.clients.slack import Slack
from ai_ticket_platform.services.content_generation.article_service import ArticleGenerationService
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

		# Initialize ChromaDB for this worker (lazy initialization)
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

		logger.info(f"[QUEUE TASK] {action} article for intent {intent_id}: {result.get('status', 'unknown')}")
		
		# Send Slack notification after successful article generation
		if result.get("status") == "success":
			try:
				article_summary = result.get("article_summary", "")
				article_title = result.get("article_title", "Untitled Article")
				
				# Build frontend URL with intent_id: {FRONTEND_URL}/cluster/{intent_id}
				frontend_url = getattr(settings, "FRONTEND_URL", None)
				if frontend_url and intent_id:
					# Remove trailing slash if present
					frontend_url = frontend_url.rstrip("/")
					article_url = f"{frontend_url}/cluster/{intent_id}"
				else:
					article_url = None
				
				if article_url and settings.SLACK_BOT_TOKEN and settings.SLACK_CHANNEL_ID:
					slack = Slack(slack_bot_token=settings.SLACK_BOT_TOKEN)
					# Format the content for Slack (title + summary)
					slack_content = f"*{article_title}*\n\n{article_summary[:500]}{'...' if len(article_summary) > 500 else ''}"
					slack_result = slack.send_new_article_proposal(
						slack_channel_id=settings.SLACK_CHANNEL_ID,
						url=article_url,
						content=slack_content
					)
					if slack_result:
						logger.info(f"[QUEUE TASK] Slack notification sent for article generation (intent {intent_id})")
					else:
						logger.warning(f"[QUEUE TASK] Failed to send Slack notification for intent {intent_id}")
				else:
					logger.warning(
						f"[QUEUE TASK] Skipping Slack notification for intent {intent_id}: "
						f"missing article_url ({article_url}), SLACK_BOT_TOKEN, or SLACK_CHANNEL_ID"
					)
			except Exception as slack_error:
				# Don't fail the article generation if Slack notification fails
				logger.error(
					f"[QUEUE TASK] Error sending Slack notification for intent {intent_id}: {slack_error}",
					exc_info=True
				)
		
		return result

	except Exception as e:
		logger.error(f"[QUEUE TASK] Error {action.lower()} article for intent {intent_id}: {e}")
		return {"status": "error", "error": str(e)}


def approve_article_task(article_id: int) -> Dict[str, Any]:
	"""
	RQ Task: Approve article.

	Args:
	    article_id: Article ID

	Returns:
	    Dict with approval result
	"""
	logger.info(f"[QUEUE TASK] Approving article {article_id}")

	try:
		settings = initialize_settings()
		AsyncSessionLocal = initialize_db_engine()

		async def approve():
			async with AsyncSessionLocal() as db:
				service = ArticleGenerationService(settings)
				result = await service.approve_article(article_id, db)
				return result

		result = _run_async(approve())

		logger.info(f"[QUEUE TASK] Approve article {article_id}: {result.get('status', 'unknown')}")
		return result

	except Exception as e:
		logger.error(f"[QUEUE TASK] Error approving article {article_id}: {e}")
		return {"status": "error", "error": str(e)}