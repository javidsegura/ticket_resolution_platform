"""Unit tests for intents router endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.routers.intents import router


@pytest.mark.asyncio
class TestGetIntents:
	"""Test GET /intents endpoint."""

	async def test_get_intents_success(self):
		"""Test successful retrieval of intents list."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent_1 = MagicMock()
		mock_intent_1.id = 1
		mock_intent_2 = MagicMock()
		mock_intent_2.id = 2

		# Intents router has 2 routes: list (index 0) and get by id (index 1)
		get_intents_endpoint = router.routes[0].endpoint

		mock_result_1 = MagicMock()
		mock_result_1.id = 1
		mock_result_2 = MagicMock()
		mock_result_2.id = 2

		# Mock article statuses
		mock_article_statuses = {
			1: {"version": 2, "status": "accepted"},
			2: {"version": 1, "status": "iteration"}
		}

		with patch("ai_ticket_platform.routers.intents.list_intents", new=AsyncMock(return_value=[mock_intent_1, mock_intent_2])):
			with patch("ai_ticket_platform.routers.intents.get_latest_article_statuses_for_intents", new=AsyncMock(return_value=mock_article_statuses)):
				with patch("ai_ticket_platform.routers.intents.IntentRead.model_validate", side_effect=[mock_result_1, mock_result_2]):
					result = await get_intents_endpoint(
						skip=0,
						limit=100,
						is_processed=None,
						db=mock_db
					)

					assert len(result) == 2
					assert result[0].id == 1
					assert result[1].id == 2

	async def test_get_intents_with_pagination(self):
		"""Test intents list with custom pagination."""
		mock_db = MagicMock(spec=AsyncSession)

		get_intents_endpoint = router.routes[0].endpoint

		with patch("ai_ticket_platform.routers.intents.list_intents", new=AsyncMock(return_value=[])):
			with patch("ai_ticket_platform.routers.intents.get_latest_article_statuses_for_intents", new=AsyncMock(return_value={})):
				result = await get_intents_endpoint(
					skip=10,
					limit=5,
					is_processed=None,
					db=mock_db
				)

				assert result == []

	async def test_get_intents_filtered_by_is_processed(self):
		"""Test intents list filtered by is_processed status."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent = MagicMock()
		mock_intent.id = 1

		get_intents_endpoint = router.routes[0].endpoint

		mock_result = MagicMock()
		mock_result.is_processed = True

		# Mock article statuses
		mock_article_statuses = {
			1: {"version": None, "status": None}
		}

		with patch("ai_ticket_platform.routers.intents.list_intents", new=AsyncMock(return_value=[mock_intent])):
			with patch("ai_ticket_platform.routers.intents.get_latest_article_statuses_for_intents", new=AsyncMock(return_value=mock_article_statuses)):
				with patch("ai_ticket_platform.routers.intents.IntentRead.model_validate", return_value=mock_result):
					result = await get_intents_endpoint(
						skip=0,
						limit=100,
						is_processed=True,
						db=mock_db
					)

					assert len(result) == 1
					assert result[0].is_processed is True


@pytest.mark.asyncio
class TestGetIntentById:
	"""Test GET /intents/{intent_id} endpoint."""

	async def test_get_intent_by_id_success(self):
		"""Test successful retrieval of intent by ID."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent = MagicMock()

		get_intent_endpoint = router.routes[1].endpoint

		mock_result = MagicMock()
		mock_result.id = 1
		mock_result.name = "Login Issues"

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			with patch("ai_ticket_platform.routers.intents.IntentRead.model_validate", return_value=mock_result):
				result = await get_intent_endpoint(
					intent_id=1,
					db=mock_db
				)

				assert result.id == 1
				assert result.name == "Login Issues"

	async def test_get_intent_by_id_not_found(self):
		"""Test retrieving non-existent intent raises 404."""
		mock_db = MagicMock(spec=AsyncSession)

		get_intent_endpoint = router.routes[1].endpoint

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=None)):
			from fastapi import HTTPException

			with pytest.raises(HTTPException) as exc_info:
				await get_intent_endpoint(
					intent_id=999,
					db=mock_db
				)

			assert exc_info.value.status_code == 404
			assert "Intent not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestGetLatestArticlesByIntent:
	"""Test GET /intents/{intent_id}/articles/latest endpoint."""

	async def test_get_latest_articles_success(self):
		"""Test successful retrieval of latest articles."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent = MagicMock()

		mock_micro_article = MagicMock()
		mock_micro_article.version = 2
		mock_micro_article.status = "accepted"
		mock_micro_article.blob_path = "articles/micro-v2.md"

		mock_full_article = MagicMock()
		mock_full_article.version = 2
		mock_full_article.status = "accepted"
		mock_full_article.blob_path = "articles/full-v2.md"

		mock_storage = MagicMock()
		mock_storage.get_presigned_url = MagicMock(side_effect=lambda path, **kwargs: f"https://storage.example.com/{path}?signed")

		get_latest_articles_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			with patch("ai_ticket_platform.routers.intents.get_latest_articles_for_intent", new=AsyncMock(return_value={"micro": mock_micro_article, "article": mock_full_article})):
				with patch("ai_ticket_platform.routers.intents.get_storage_service", return_value=mock_storage):
					result = await get_latest_articles_endpoint(
						intent_id=1,
						db=mock_db
					)

					assert result.intent_id == 1
					assert result.version == 2
					assert result.status == "accepted"
					assert "https://storage.example.com/articles/micro-v2.md" in result.presigned_url_micro
					assert "https://storage.example.com/articles/full-v2.md" in result.presigned_url_full

	async def test_get_latest_articles_intent_not_found(self):
		"""Test retrieving articles for non-existent intent."""
		mock_db = MagicMock(spec=AsyncSession)

		get_latest_articles_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=None)):
			from fastapi import HTTPException

			with pytest.raises(HTTPException) as exc_info:
				await get_latest_articles_endpoint(
					intent_id=999,
					db=mock_db
				)

			assert exc_info.value.status_code == 404
			assert "Intent not found" in str(exc_info.value.detail)

	async def test_get_latest_articles_no_articles_exist(self):
		"""Test retrieving articles when none exist for intent."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent = MagicMock()

		get_latest_articles_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			with patch("ai_ticket_platform.routers.intents.get_latest_articles_for_intent", new=AsyncMock(return_value={"micro": None, "article": None})):
				result = await get_latest_articles_endpoint(
					intent_id=1,
					db=mock_db
				)

				assert result.intent_id == 1
				assert result.version is None
				assert result.status is None
				assert result.presigned_url_micro is None
				assert result.presigned_url_full is None

	async def test_get_latest_articles_only_micro_exists(self):
		"""Test retrieving articles when only micro article exists."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent = MagicMock()

		mock_micro_article = MagicMock()
		mock_micro_article.version = 1
		mock_micro_article.status = "iteration"
		mock_micro_article.blob_path = "articles/micro-v1.md"

		mock_storage = MagicMock()
		mock_storage.get_presigned_url = MagicMock(return_value="https://storage.example.com/signed-url")

		get_latest_articles_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			with patch("ai_ticket_platform.routers.intents.get_latest_articles_for_intent", new=AsyncMock(return_value={"micro": mock_micro_article, "article": None})):
				with patch("ai_ticket_platform.routers.intents.get_storage_service", return_value=mock_storage):
					result = await get_latest_articles_endpoint(
						intent_id=1,
						db=mock_db
					)

					assert result.version == 1
					assert result.status == "iteration"
					assert result.presigned_url_micro is not None
					assert result.presigned_url_full is None

	async def test_get_latest_articles_only_full_article_exists(self):
		"""Test retrieving articles when only full article exists."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent = MagicMock()

		mock_full_article = MagicMock()
		mock_full_article.version = 3
		mock_full_article.status = "accepted"
		mock_full_article.blob_path = "articles/full-v3.md"

		mock_storage = MagicMock()
		mock_storage.get_presigned_url = MagicMock(return_value="https://storage.example.com/signed-url")

		get_latest_articles_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			with patch("ai_ticket_platform.routers.intents.get_latest_articles_for_intent", new=AsyncMock(return_value={"micro": None, "article": mock_full_article})):
				with patch("ai_ticket_platform.routers.intents.get_storage_service", return_value=mock_storage):
					result = await get_latest_articles_endpoint(
						intent_id=1,
						db=mock_db
					)

					assert result.version == 3
					assert result.status == "accepted"
					assert result.presigned_url_micro is None
					assert result.presigned_url_full is not None

	async def test_get_latest_articles_presigned_url_error_handling(self):
		"""Test that presigned URL generation errors are handled gracefully."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent = MagicMock()

		mock_micro_article = MagicMock()
		mock_micro_article.version = 1
		mock_micro_article.status = "accepted"
		mock_micro_article.blob_path = "articles/micro-v1.md"

		mock_storage = MagicMock()
		mock_storage.get_presigned_url = MagicMock(side_effect=Exception("Storage error"))

		get_latest_articles_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			with patch("ai_ticket_platform.routers.intents.get_latest_articles_for_intent", new=AsyncMock(return_value={"micro": mock_micro_article, "article": None})):
				with patch("ai_ticket_platform.routers.intents.get_storage_service", return_value=mock_storage):
					result = await get_latest_articles_endpoint(
						intent_id=1,
						db=mock_db
					)

					# Should not raise exception, but return None for failed URLs
					assert result.version == 1
					assert result.presigned_url_micro is None

	async def test_get_latest_articles_full_article_presigned_url_error(self):
		"""Test that full article presigned URL generation errors are handled gracefully."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_intent = MagicMock()

		mock_full_article = MagicMock()
		mock_full_article.version = 2
		mock_full_article.status = "accepted"
		mock_full_article.blob_path = "articles/full-v2.md"

		mock_storage = MagicMock()
		mock_storage.get_presigned_url = MagicMock(side_effect=Exception("Storage error"))

		get_latest_articles_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.intents.get_intent", new=AsyncMock(return_value=mock_intent)):
			with patch("ai_ticket_platform.routers.intents.get_latest_articles_for_intent", new=AsyncMock(return_value={"micro": None, "article": mock_full_article})):
				with patch("ai_ticket_platform.routers.intents.get_storage_service", return_value=mock_storage):
					result = await get_latest_articles_endpoint(
						intent_id=1,
						db=mock_db
					)

					# Should not raise exception, but return None for failed URLs
					assert result.version == 2
					assert result.presigned_url_full is None
					assert result.presigned_url_micro is None
