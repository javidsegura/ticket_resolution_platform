import logging
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.database.CRUD.article import create_article, get_article_by_id as read_article
from ai_ticket_platform.database.CRUD.intents import get_intent, update_intent
from ai_ticket_platform.database.CRUD.ticket import list_tickets_by_intent
from ai_ticket_platform.core.clients import azure_search
from ai_ticket_platform.services.content_generation.langgraph_rag_workflow import RAGWorkflow

logger = logging.getLogger(__name__)


class ArticleGenerationService:
	"""Service for generating and iterating articles using RAG."""

	def __init__(self, settings):
		"""
		Initialize article generation service.

		Args:
		    settings: Application settings
		"""
		self.settings = settings
		self.rag_workflow = RAGWorkflow(azure_search, settings)

	async def generate_article(
		self,
		intent_id: int,
		db: AsyncSession,
		feedback: Optional[str] = None,
		previous_article_id: Optional[int] = None,
	) -> Dict:
		"""
		Generate or iterate article for an intent.

		If feedback is provided, this is an iteration. Otherwise, initial generation.
		"""
		is_iteration = feedback is not None

		if is_iteration:
			logger.info(
				f"Iterating article for intent {intent_id} with feedback: {feedback[:50]}..."
			)
		else:
			logger.info(f"Generating initial article for intent {intent_id}")

		try:
			# 1. Fetch intent
			intent = await get_intent(db, intent_id)
			if not intent:
				return {"status": "error", "error": "Intent not found"}

			# 2. Fetch tickets
			tickets = await list_tickets_by_intent(db, intent_id)
			if not tickets:
				return {
					"status": "error",
					"error": "No tickets found for this intent",
				}

			# 3. Prepare RAG input
			ticket_summaries = [
				f"{ticket.subject}: {ticket.body[:200]}" for ticket in tickets
			]

			rag_input = {
				"intent_id": intent_id,
				"intent_name": intent.name,
				"ticket_summaries": ticket_summaries,
				"area": intent.area or "",
				"is_iteration": is_iteration,
			}

			# Add iteration-specific fields if applicable
			if is_iteration and previous_article_id:
				previous_article = await read_article(db, previous_article_id)
				if previous_article:
					rag_input["previous_article_content"] = previous_article.content
					rag_input["previous_article_title"] = previous_article.title
					rag_input["human_feedback"] = feedback

			# 4. Run RAG workflow
			logger.info(
				f"Running RAG workflow for intent {intent_id} (iteration: {is_iteration})"
			)

			rag_result = await self.rag_workflow.run(rag_input)

			if not rag_result or "error" in rag_result:
				return {
					"status": "error",
					"error": rag_result.get("error", "RAG workflow failed"),
				}

			# 5. Create Article record
			version = 1
			if is_iteration and previous_article_id:
				previous_article = await read_article(db, previous_article_id)
				if previous_article:
					version = previous_article.version + 1

			article = await create_article(
				db,
				intent_id=intent_id,
				title=rag_result.get("article_title", "Untitled"),
				content=rag_result.get("article_content", ""),
				type="article",
				status="iteration",  # Always starts as iteration
				version=version,
				feedback=feedback,  # Store feedback if iteration
			)

			logger.info(f"Created article {article.id} (version {version})")

			# 6. Update Intent
			await update_intent(
				db,
				intent_id,
				{
					"is_processed": True,
				},
			)

			logger.info(f"Updated intent {intent_id}: is_processed=True")

			return {
				"status": "success",
				"article_id": article.id,
				"intent_id": intent_id,
				"version": version,
				"is_iteration": is_iteration,
				"confidence_score": rag_result.get("confidence_score", 0.0),
			}

		except Exception as e:
			logger.error(
				f"Error generating article for intent {intent_id}: {e}", exc_info=True
			)
			return {"status": "error", "error": str(e)}

	async def approve_article(self, article_id: int, db: AsyncSession) -> Dict:
		"""
		Approve article - change status to "accepted".
		"""
		logger.info(f"Approving article {article_id}")

		try:
			article = await read_article(db, article_id)

			if not article:
				return {"status": "error", "error": "Article not found"}

			# Update status
			article.status = "accepted"
			await db.commit()
			await db.refresh(article)

			logger.info(f"Article {article_id} approved successfully")

			return {
				"status": "success",
				"article_id": article_id,
				"new_status": "accepted",
			}

		except Exception as e:
			logger.error(f"Error approving article {article_id}: {e}")
			return {"status": "error", "error": str(e)}
