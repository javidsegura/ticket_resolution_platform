from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import logging
from rq import Queue

from ai_ticket_platform.dependencies import get_db
from ai_ticket_platform.dependencies.queue import get_queue
from ai_ticket_platform.database.CRUD.article import (
	get_article_by_id,
	update_article,
)
from ai_ticket_platform.schemas.endpoints.article import ArticleRead
from ai_ticket_platform.services.content_generation.content_generation_interface import (
	generate_article_task,
)
from ai_ticket_platform.services.content_generation.article_service import (
	ArticleGenerationService,
)
from ai_ticket_platform.dependencies import get_app_settings

router = APIRouter(prefix="/articles", tags=["articles"])
logger = logging.getLogger(__name__)


class IterateArticleRequest(BaseModel):
	"""Request body for iterating an article with feedback."""

	feedback: str


@router.post("/{article_id}/approve")
async def approve_article(
	article_id: int,
	db: AsyncSession = Depends(get_db),
	settings=Depends(get_app_settings),
):
	"""
	Approve an article and mark it as accepted.

	Approves both the micro (summary) and article (full content) of the same version.
	Sets status to "accepted" and clears feedback.

	Args:
	    article_id: ID of the article to approve
	    db: Database session
	    settings: Application settings

	Returns:
	    Success response with approval details
	"""
	logger.info(f"[ARTICLE APPROVE] Approving article {article_id}")

	try:
		# Verify article exists
		article = await get_article_by_id(db, article_id)
		if not article:
			raise HTTPException(status_code=404, detail="Article not found")

		# Approve article
		service = ArticleGenerationService(settings)
		result = await service.approve_article(article_id, db)

		if result.get("status") == "error":
			logger.error(
				f"[ARTICLE APPROVE] Approval failed for article {article_id}: {result.get('error')}"
			)
			raise HTTPException(
				status_code=500, detail=result.get("error", "Approval failed")
			)

		logger.info(f"[ARTICLE APPROVE] Successfully approved article {article_id}")

		return {
			"status": "success",
			"message": f"Article {article_id} approved successfully",
			"article_id": article_id,
			"intent_id": result.get("intent_id"),
			"version": result.get("version"),
			"new_status": result.get("new_status"),
			"approved_types": result.get("approved_types", []),
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(
			f"[ARTICLE APPROVE] Error approving article {article_id}: {e}",
			exc_info=True,
		)
		raise HTTPException(status_code=500, detail=str(e))


@router.post("/{article_id}/iterate")
async def iterate_article(
	article_id: int,
	request: IterateArticleRequest,
	queue: Queue = Depends(get_queue),
	db: AsyncSession = Depends(get_db),
):
	"""
	Iterate on an article by providing feedback for regeneration.

	Saves the feedback to the current article and queues a new generation job.
	The RAG service will use the feedback to generate an improved version.

	Args:
	    article_id: ID of the article to iterate on
	    request: Request containing feedback text
	    queue: RQ queue for task execution
	    db: Database session

	Returns:
	    Success response with new generation job details
	"""
	logger.info(f"[ARTICLE ITERATE] Starting iteration for article {article_id}")
	try:
		# Verify article exists
		article = await get_article_by_id(db, article_id)
		if not article:
			raise HTTPException(status_code=404, detail="Article not found")

		intent_id = article.intent_id
		version = article.version

		# Enqueue generation job FIRST to ensure task is queued before DB update
		# This prevents inconsistent state if enqueue fails after DB update
		generation_job = queue.enqueue(
			generate_article_task,
			intent_id=intent_id,
			feedback=request.feedback,
			previous_article_id=article_id,
			job_timeout="15m",
		)

		logger.info(
			f"[ARTICLE ITERATE] Enqueued generation job {generation_job.id} "
			f"for intent {intent_id}. Will generate version {version + 1}"
		)

		# Update the article with feedback AFTER successful enqueue
		updated_article = await update_article(
			db, article_id, feedback=request.feedback
		)

		if not updated_article:
			logger.error(
				f"[ARTICLE ITERATE] Failed to update article {article_id} with feedback "
				f"after enqueuing job {generation_job.id}. Job will still process."
			)
			raise HTTPException(
				status_code=500,
				detail="Generation job queued but failed to save feedback to article",
			)

		logger.info(f"[ARTICLE ITERATE] Updated article {article_id} with feedback")

		return {
			"status": "success",
			"message": f"Iteration queued for article {article_id}",
			"article_id": article_id,
			"intent_id": intent_id,
			"current_version": version,
			"next_version": version + 1,
			"feedback_saved": True,
			"job_id": generation_job.id,
		}

	except HTTPException:
		raise
	except Exception as e:
		logger.error(
			f"[ARTICLE ITERATE] Error iterating article {article_id}: {e}",
			exc_info=True,
		)
		raise HTTPException(status_code=500, detail=str(e))
