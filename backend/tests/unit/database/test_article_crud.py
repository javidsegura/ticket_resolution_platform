"""Unit tests for article CRUD operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ai_ticket_platform.database.CRUD.article import (
	create_article,
	get_article_by_id,
	get_all_articles,
	update_article,
	delete_article,
	get_articles_by_intent,
	get_latest_articles_for_intent,
)


@pytest.mark.asyncio
class TestCreateArticle:
	"""Test create_article operation."""

	async def test_create_article_success(self):
		"""Test successful article creation."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.article.Article") as mock_article_class:
			mock_article = MagicMock()
			mock_article.id = 1
			mock_article_class.return_value = mock_article

			result = await create_article(
				db=mock_db,
				intent_id=5,
				type="micro",
				blob_path="articles/article-1-v1-micro.md",
				status="iteration",
				version=1,
				feedback="Good summary"
			)

			assert result == mock_article
			mock_db.add.assert_called_once_with(mock_article)
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once_with(mock_article)
			mock_db.rollback.assert_not_called()

	async def test_create_article_defaults(self):
		"""Test article creation with default values."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock()
		mock_db.refresh = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.article.Article") as mock_article_class:
			mock_article = MagicMock()
			mock_article_class.return_value = mock_article

			result = await create_article(
				db=mock_db,
				intent_id=5,
				type="article",
				blob_path="articles/article-1-v1-full.md"
			)

			assert result == mock_article
			call_kwargs = mock_article_class.call_args[1]
			assert call_kwargs["status"] == "iteration"
			assert call_kwargs["version"] == 1
			assert call_kwargs["feedback"] is None

	async def test_create_article_database_error(self):
		"""Test handling of database errors during article creation."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_db.add = MagicMock()
		mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB Error"))
		mock_db.rollback = AsyncMock()

		with patch("ai_ticket_platform.database.CRUD.article.Article"):
			with pytest.raises(RuntimeError, match="Failed to create article"):
				await create_article(
					db=mock_db,
					intent_id=5,
					type="micro",
					blob_path="articles/test.md"
				)

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestGetArticleById:
	"""Test get_article_by_id operation."""

	async def test_get_article_found(self):
		"""Test successful retrieval of article by ID."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article = MagicMock()
		mock_article.id = 1
		mock_article.type = "micro"

		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=mock_article)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_article_by_id(db=mock_db, article_id=1)

		assert result == mock_article
		assert result.id == 1
		mock_db.execute.assert_called_once()

	async def test_get_article_not_found(self):
		"""Test article not found returns None."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_result = MagicMock()
		mock_result.scalar_one_or_none = MagicMock(return_value=None)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_article_by_id(db=mock_db, article_id=999)

		assert result is None
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestGetAllArticles:
	"""Test get_all_articles operation."""

	async def test_get_all_articles_default_pagination(self):
		"""Test retrieving all articles with default pagination."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article_1 = MagicMock(id=1, type="micro")
		mock_article_2 = MagicMock(id=2, type="article")

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_article_1, mock_article_2])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_articles(db=mock_db)

		assert len(result) == 2
		assert result[0].id == 1
		assert result[1].id == 2
		mock_db.execute.assert_called_once()

	async def test_get_all_articles_custom_pagination(self):
		"""Test retrieving articles with custom skip and limit."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_all_articles(db=mock_db, skip=10, limit=5)

		assert result == []
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestUpdateArticle:
	"""Test update_article operation."""

	async def test_update_article_status(self):
		"""Test updating article status."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article = MagicMock()
		mock_article.id = 1
		mock_article.status = "iteration"

		with patch("ai_ticket_platform.database.CRUD.article.get_article_by_id", new=AsyncMock(return_value=mock_article)):
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			result = await update_article(db=mock_db, article_id=1, status="published")

			assert result == mock_article
			assert result.status == "published"
			mock_db.commit.assert_called_once()
			mock_db.refresh.assert_called_once()

	async def test_update_article_version(self):
		"""Test updating article version."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article = MagicMock()
		mock_article.id = 1
		mock_article.version = 1

		with patch("ai_ticket_platform.database.CRUD.article.get_article_by_id", new=AsyncMock(return_value=mock_article)):
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			result = await update_article(db=mock_db, article_id=1, version=2)

			assert result == mock_article
			assert result.version == 2
			mock_db.commit.assert_called_once()

	async def test_update_article_feedback(self):
		"""Test updating article feedback."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article = MagicMock()
		mock_article.id = 1
		mock_article.feedback = None

		with patch("ai_ticket_platform.database.CRUD.article.get_article_by_id", new=AsyncMock(return_value=mock_article)):
			mock_db.commit = AsyncMock()
			mock_db.refresh = AsyncMock()

			result = await update_article(db=mock_db, article_id=1, feedback="Needs revision")

			assert result == mock_article
			assert result.feedback == "Needs revision"
			mock_db.commit.assert_called_once()

	async def test_update_article_not_found(self):
		"""Test updating article that doesn't exist."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.database.CRUD.article.get_article_by_id", new=AsyncMock(return_value=None)):
			result = await update_article(db=mock_db, article_id=999, status="published")

			assert result is None

	async def test_update_article_database_error(self):
		"""Test handling database error during update."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article = MagicMock()

		with patch("ai_ticket_platform.database.CRUD.article.get_article_by_id", new=AsyncMock(return_value=mock_article)):
			mock_db.commit = AsyncMock(side_effect=SQLAlchemyError("DB Error"))
			mock_db.rollback = AsyncMock()

			with pytest.raises(RuntimeError, match="Failed to update article"):
				await update_article(db=mock_db, article_id=1, status="published")

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestDeleteArticle:
	"""Test delete_article operation."""

	async def test_delete_article_success(self):
		"""Test successful article deletion."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article = MagicMock()
		mock_article.id = 1

		with patch("ai_ticket_platform.database.CRUD.article.get_article_by_id", new=AsyncMock(return_value=mock_article)):
			mock_db.delete = AsyncMock()
			mock_db.commit = AsyncMock()

			result = await delete_article(db=mock_db, article_id=1)

			assert result is True
			mock_db.delete.assert_called_once_with(mock_article)
			mock_db.commit.assert_called_once()

	async def test_delete_article_not_found(self):
		"""Test deleting article that doesn't exist."""
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.database.CRUD.article.get_article_by_id", new=AsyncMock(return_value=None)):
			result = await delete_article(db=mock_db, article_id=999)

			assert result is False

	async def test_delete_article_database_error(self):
		"""Test handling database error during deletion."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article = MagicMock()

		with patch("ai_ticket_platform.database.CRUD.article.get_article_by_id", new=AsyncMock(return_value=mock_article)):
			mock_db.delete = AsyncMock(side_effect=SQLAlchemyError("DB Error"))
			mock_db.rollback = AsyncMock()

			with pytest.raises(RuntimeError, match="Failed to delete article"):
				await delete_article(db=mock_db, article_id=1)

			mock_db.rollback.assert_called_once()


@pytest.mark.asyncio
class TestGetArticlesByIntent:
	"""Test get_articles_by_intent operation."""

	async def test_get_articles_by_intent_found(self):
		"""Test retrieving articles for specific intent."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_article_1 = MagicMock(id=1, intent_id=5, version=2, type="micro")
		mock_article_2 = MagicMock(id=2, intent_id=5, version=2, type="article")
		mock_article_3 = MagicMock(id=3, intent_id=5, version=1, type="micro")

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_article_1, mock_article_2, mock_article_3])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_articles_by_intent(db=mock_db, intent_id=5)

		assert len(result) == 3
		mock_db.execute.assert_called_once()

	async def test_get_articles_by_intent_empty(self):
		"""Test retrieving articles when intent has none."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[])
		mock_result = MagicMock()
		mock_result.scalars = MagicMock(return_value=mock_scalars)
		mock_db.execute = AsyncMock(return_value=mock_result)

		result = await get_articles_by_intent(db=mock_db, intent_id=999)

		assert result == []
		mock_db.execute.assert_called_once()


@pytest.mark.asyncio
class TestGetLatestArticlesForIntent:
	"""Test get_latest_articles_for_intent operation."""

	async def test_get_latest_articles_both_types(self):
		"""Test retrieving latest articles for both micro and full types."""
		mock_db = MagicMock(spec=AsyncSession)

		# Mock max version query
		mock_max_result = MagicMock()
		mock_max_result.scalar = MagicMock(return_value=2)

		# Mock articles query
		mock_article_micro = MagicMock(id=1, intent_id=5, version=2, type="micro")
		mock_article_full = MagicMock(id=2, intent_id=5, version=2, type="article")

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_article_full, mock_article_micro])
		mock_articles_result = MagicMock()
		mock_articles_result.scalars = MagicMock(return_value=mock_scalars)

		mock_db.execute = AsyncMock(side_effect=[mock_max_result, mock_articles_result])

		result = await get_latest_articles_for_intent(db=mock_db, intent_id=5)

		assert result["micro"] == mock_article_micro
		assert result["article"] == mock_article_full
		assert mock_db.execute.call_count == 2

	async def test_get_latest_articles_one_type_missing(self):
		"""Test retrieving latest articles when only one type exists."""
		mock_db = MagicMock(spec=AsyncSession)

		# Mock max version query
		mock_max_result = MagicMock()
		mock_max_result.scalar = MagicMock(return_value=1)

		# Mock articles query - only micro type
		mock_article_micro = MagicMock(id=1, intent_id=5, version=1, type="micro")

		mock_scalars = MagicMock()
		mock_scalars.all = MagicMock(return_value=[mock_article_micro])
		mock_articles_result = MagicMock()
		mock_articles_result.scalars = MagicMock(return_value=mock_scalars)

		mock_db.execute = AsyncMock(side_effect=[mock_max_result, mock_articles_result])

		result = await get_latest_articles_for_intent(db=mock_db, intent_id=5)

		assert result["micro"] == mock_article_micro
		assert result["article"] is None
		assert mock_db.execute.call_count == 2

	async def test_get_latest_articles_no_articles(self):
		"""Test retrieving latest articles when none exist."""
		mock_db = MagicMock(spec=AsyncSession)

		# Mock max version query returning None
		mock_max_result = MagicMock()
		mock_max_result.scalar = MagicMock(return_value=None)

		mock_db.execute = AsyncMock(return_value=mock_max_result)

		result = await get_latest_articles_for_intent(db=mock_db, intent_id=999)

		assert result["micro"] is None
		assert result["article"] is None
		assert mock_db.execute.call_count == 1
