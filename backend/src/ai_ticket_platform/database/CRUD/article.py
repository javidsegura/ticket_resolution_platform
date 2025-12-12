from sqlalchemy import select, func
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.database.generated_models import Article, Intent


async def create_article(
	db: AsyncSession,
	intent_id: int,
	type: str,
	blob_path: str,
	status: str = "iteration",
	version: int = 1,
	feedback: Optional[str] = None,
) -> Article:
	"""
	Create a new article with blob reference.

	Args:
	    db: Database session
	    intent_id: Intent ID (immutable after creation)
	    type: Article type ('micro' for summary, 'article' for full content)
	    blob_path: Azure Blob Storage path (e.g., 'articles/article-1-v1-micro-2024-01-15T10:30:00Z.md')
	    status: Article status (default 'iteration')
	    version: Version number (default 1)
	    feedback: Optional feedback text

	Note: Content is stored in Azure Blob Storage, blob_path is reference to blob location.
	"""
	db_article = Article(
		intent_id=intent_id,
		type=type,
		blob_path=blob_path,
		status=status,
		version=version,
		feedback=feedback,
	)
	try:
		db.add(db_article)
		await db.commit()
		await db.refresh(db_article)
	except SQLAlchemyError as e:
		await db.rollback()
		raise RuntimeError(f"Failed to create article: {e}") from e
	return db_article


async def get_article_by_id(db: AsyncSession, article_id: int) -> Optional[Article]:
	"""
	Retrieve an article by ID.
	"""
	result = await db.execute(select(Article).where(Article.id == article_id))
	return result.scalar_one_or_none()


async def get_all_articles(
	db: AsyncSession, skip: int = 0, limit: int = 100
) -> List[Article]:
	"""
	Retrieve all articles.
	"""
	result = await db.execute(
		select(Article).offset(skip).limit(limit).order_by(Article.created_at.desc())
	)
	return result.scalars().all()


async def update_article(
	db: AsyncSession,
	article_id: int,
	status: Optional[str] = None,
	version: Optional[int] = None,
	feedback: Optional[str] = None,
) -> Optional[Article]:
	"""
	Update an article. Only status, version, and feedback can be updated.

	Note: intent_id, type, and blob_path are immutable to protect core article data.
	"""
	article = await get_article_by_id(db, article_id)

	if not article:
		return None

	if status is not None:
		article.status = status
	if version is not None:
		article.version = version
	if feedback is not None:
		article.feedback = feedback

	try:
		await db.commit()
		await db.refresh(article)
	except SQLAlchemyError as e:
		await db.rollback()
		raise RuntimeError(f"Failed to update article: {e}") from e

	return article


async def delete_article(db: AsyncSession, article_id: int) -> bool:
	"""
	Delete an article by ID.
	"""
	article = await get_article_by_id(db, article_id)
	if article:
		try:
			await db.delete(article)
			await db.commit()
		except SQLAlchemyError as e:
			await db.rollback()
			raise RuntimeError(f"Failed to delete article: {e}") from e
		return True
	return False


async def get_articles_by_intent(
	db: AsyncSession, intent_id: int
) -> List[Article]:
	"""
	Get all articles for a specific intent.

	Returns a list of all articles (all versions, both micro and article types).
	"""
	query = (
		select(Article)
		.where(Article.intent_id == intent_id)
		.order_by(Article.version.desc(), Article.type)
	)
	result = await db.execute(query)
	return result.scalars().all()


async def get_latest_articles_for_intent(
	db: AsyncSession, intent_id: int
) -> Dict[str, Optional[Article]]:
	"""
	Get the latest version articles (both micro and full) for a specific intent.

	Returns a dictionary with 'micro' and 'article' keys.
	Example: {'micro': Article(...), 'article': Article(...)}
	"""
	# Get the maximum version for this intent
	max_version_query = select(func.max(Article.version)).where(
		Article.intent_id == intent_id
	)
	result = await db.execute(max_version_query)
	max_version = result.scalar()

	if max_version is None:
		return {"micro": None, "article": None}

	# Get both micro and article for the latest version
	query = (
		select(Article)
		.where(Article.intent_id == intent_id, Article.version == max_version)
		.order_by(Article.type)
	)

	result = await db.execute(query)
	articles = result.scalars().all()

	# Organize by type
	articles_dict: Dict[str, Optional[Article]] = {"micro": None, "article": None}
	for article in articles:
		articles_dict[article.type] = article

	return articles_dict


async def get_latest_article_statuses_for_intents(
	db: AsyncSession, intent_ids: List[int]
) -> Dict[int, Dict[str, Optional[int | str]]]:
	"""
	Get the latest article status and version for multiple intents in a single query.

	This is optimized to avoid N+1 query problems when fetching statuses for many intents.

	Args:
		db: Database session
		intent_ids: List of intent IDs to fetch article statuses for

	Returns:
		Dictionary mapping intent_id to a dict with 'version' and 'status' keys.
		Example: {1: {'version': 2, 'status': 'accepted'}, 2: {'version': None, 'status': None}}
	"""
	if not intent_ids:
		return {}

	# Subquery to get max version per intent
	max_version_subq = (
		select(
			Article.intent_id,
			func.max(Article.version).label("max_version"),
		)
		.where(Article.intent_id.in_(intent_ids))
		.group_by(Article.intent_id)
		.subquery()
	)

	# Get the latest article for each intent, preferring 'article' type over 'micro'
	# Order by type ASC so 'article' (alphabetically first) comes before 'micro'
	latest_articles_query = (
		select(
			Article.intent_id,
			Article.version,
			Article.status,
			Article.type,
		)
		.join(
			max_version_subq,
			(Article.intent_id == max_version_subq.c.intent_id)
			& (Article.version == max_version_subq.c.max_version),
		)
		.where(Article.intent_id.in_(intent_ids))
		.order_by(Article.intent_id, Article.type.asc())  # 'article' comes before 'micro' alphabetically
	)

	result = await db.execute(latest_articles_query)
	rows = result.all()

	# Build result dictionary, preferring 'article' type over 'micro'
	# Since we ordered by type ASC, 'article' will come first for each intent_id
	statuses: Dict[int, Dict[str, Optional[int | str]]] = {}
	for intent_id, version, status, article_type in rows:
		# Store the first row for each intent_id (which will be 'article' if it exists)
		if intent_id not in statuses:
			statuses[intent_id] = {
				"version": version,
				"status": status,
			}

	# Add entries for intents with no articles
	for intent_id in intent_ids:
		if intent_id not in statuses:
			statuses[intent_id] = {"version": None, "status": None}

	return statuses
