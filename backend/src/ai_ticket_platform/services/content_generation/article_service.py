import logging
from typing import Dict, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.database.CRUD.article import create_article, get_article_by_id as read_article
from ai_ticket_platform.database.CRUD.intents import get_intent, update_intent
from ai_ticket_platform.database.CRUD.ticket import list_tickets_by_intent
from ai_ticket_platform.database.generated_models import Article
from ai_ticket_platform.core.clients import azure_search
from ai_ticket_platform.services.content_generation.langgraph_rag_workflow import RAGWorkflow
from ai_ticket_platform.services.storage.azure import AzureBlobStorage

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
		Creates 2 articles: MICRO (summary) and ARTICLE (full content) with same version number.
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
					# Note: Content is stored in Azure Blob, need to download BOTH micro and article
					try:
						storage = AzureBlobStorage("articles")

						# Get the version of the previous article
						prev_version = previous_article.version

						# Find BOTH micro and article for the same intent and previous version
						# Query all articles for this intent and version
						articles_for_version = await db.execute(
							select(Article).where(
								(Article.intent_id == intent_id) &
								(Article.version == prev_version)
							)
						)
						articles_prev = articles_for_version.scalars().all()

						# Separate micro and article
						micro_article = None
						article_article = None
						article_title = "Untitled Article"

						for art in articles_prev:
							if art.type == "micro":
								micro_article = art
							elif art.type == "article":
								article_article = art

						# Download and parse MICRO (summary)
						if micro_article:
							blob_content_micro = storage.download_blob(micro_article.blob_path)
							lines = blob_content_micro.split('\n', 2)
							article_title = lines[0].replace('# ', '').strip() if lines else "Untitled"
							summary_text = lines[2] if len(lines) > 2 else ""
							rag_input["previous_article_title"] = article_title
							rag_input["previous_article_summary"] = summary_text
							logger.info(f"Loaded previous MICRO article {micro_article.id} from blob")

						# Download and parse ARTICLE (full content)
						if article_article:
							blob_content_article = storage.download_blob(article_article.blob_path)
							lines = blob_content_article.split('\n', 2)
							content_text = lines[2] if len(lines) > 2 else ""
							rag_input["previous_article_content"] = content_text
							logger.info(f"Loaded previous ARTICLE article {article_article.id} from blob")

						# Pass feedback and iteration info
						rag_input["human_feedback"] = feedback
						rag_input["iteration_number"] = prev_version + 1
						rag_input["is_iteration"] = True

						logger.info(f"Loaded both MICRO and ARTICLE from version {prev_version} for iteration")
					except Exception as e:
						logger.error(f"Failed to load previous article content from blobs: {e}", exc_info=True)
						raise

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

			# 5. Calculate version number
			version = 1
			if is_iteration and previous_article_id:
				previous_article = await read_article(db, previous_article_id)
				if previous_article:
					version = previous_article.version + 1

			# 6. Prepare Azure Blob Storage uploads
			try:
				storage = AzureBlobStorage("articles")
				timestamp = datetime.utcnow().isoformat() + "Z"

				# Extract RAG output
				article_title = rag_result.get("article_title", "Untitled Article")
				article_summary = rag_result.get("article_summary", "")
				article_content = rag_result.get("article_content", "")

				# 6a. Upload MICRO (summary)
				blob_name_micro = f"articles/article-{intent_id}-v{version}-micro-{timestamp}.md"
				content_micro = f"# {article_title}\n\n{article_summary}"
				blob_path_micro = storage.upload_blob(blob_name_micro, content_micro)
				logger.info(f"Uploaded MICRO blob: {blob_path_micro}")

				# 6b. Upload ARTICLE (full content)
				blob_name_article = f"articles/article-{intent_id}-v{version}-article-{timestamp}.md"
				content_article = f"# {article_title}\n\n{article_content}"
				blob_path_article = storage.upload_blob(blob_name_article, content_article)
				logger.info(f"Uploaded ARTICLE blob: {blob_path_article}")

			except Exception as e:
				logger.error(f"Failed to upload blobs to Azure: {e}", exc_info=True)
				raise

			# 7. Create new Article records in database (MICRO) - new versions have NO feedback initially
			article_micro = await create_article(
				db,
				intent_id=intent_id,
				type="micro",
				blob_path=blob_path_micro,
				status="iteration",
				version=version,
				feedback=None,  # New versions start without feedback
			)
			logger.info(f"Created MICRO article {article_micro.id} (version {version})")

			# 9. Create new Article records in database (ARTICLE) - new versions have NO feedback initially
			article_article = await create_article(
				db,
				intent_id=intent_id,
				type="article",
				blob_path=blob_path_article,
				status="iteration",
				version=version,
				feedback=None,  # New versions start without feedback
			)
			logger.info(f"Created ARTICLE article {article_article.id} (version {version})")

			# 10. Update Intent
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
				"article_micro_id": article_micro.id,
				"article_article_id": article_article.id,
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
		Approve article - change status to "accepted" for both micro and article of same version.

		Approving an article means approving BOTH the micro (summary) and article (full content)
		of the same version together. Status is set to "accepted" and feedback is cleared.
		"""
		logger.info(f"Approving article {article_id}")

		try:
			# Get the article to find its intent_id and version
			article = await read_article(db, article_id)

			if not article:
				return {"status": "error", "error": "Article not found"}

			intent_id = article.intent_id
			version = article.version

			# Find both MICRO and ARTICLE for the same intent and version
			articles_to_approve = await db.execute(
				select(Article).where(
					(Article.intent_id == intent_id) &
					(Article.version == version)
				)
			)
			articles = articles_to_approve.scalars().all()

			if not articles:
				return {"status": "error", "error": "No articles found for this version"}

			# Update all articles (both micro and article) to accepted status
			for art in articles:
				art.status = "accepted"
				art.feedback = None  # Clear feedback when approving

			await db.commit()

			# Refresh articles
			for art in articles:
				await db.refresh(art)

			approved_types = [art.type for art in articles]
			logger.info(f"Approved {len(articles)} articles (types: {approved_types}) for intent {intent_id} version {version}")

			return {
				"status": "success",
				"article_id": article_id,
				"intent_id": intent_id,
				"version": version,
				"approved_types": approved_types,
				"new_status": "accepted",
			}

		except Exception as e:
			logger.error(f"Error approving article {article_id}: {e}", exc_info=True)
			return {"status": "error", "error": str(e)}
