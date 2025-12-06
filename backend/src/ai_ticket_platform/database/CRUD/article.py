from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.database.generated_models import Article


async def create_article(
    db: AsyncSession,
    intent_id: int,
    type: str,
    blob_path: str,
    status: str = "iteration",
    version: int = 1,
    feedback: Optional[str] = None
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
