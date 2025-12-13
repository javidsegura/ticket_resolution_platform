import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from ai_ticket_platform.routers.articles import approve_article, iterate_article, IterateArticleRequest


@pytest.fixture
def mock_db():
	"""Mock database session"""
	return AsyncMock()


@pytest.fixture
def mock_settings():
	"""Mock application settings"""
	settings = MagicMock()
	settings.SLACK_BOT_TOKEN = "test-token"
	settings.SLACK_CHANNEL_ID = "test-channel"
	return settings


@pytest.fixture
def mock_queue():
	"""Mock RQ queue"""
	queue = MagicMock()
	job = MagicMock()
	job.id = "test-job-123"
	queue.enqueue.return_value = job
	return queue


@pytest.mark.asyncio
async def test_approve_article_success(mock_db, mock_settings):
	"""Test successful article approval"""
	article_id = 1
	mock_article = MagicMock()
	mock_article.id = article_id
	mock_article.intent_id = 10
	mock_article.version = 1

	approval_result = {
		"status": "success",
		"intent_id": 10,
		"version": 1,
		"new_status": "accepted",
		"approved_types": ["article", "micro"],
	}

	with (
		patch(
			"ai_ticket_platform.routers.articles.get_article_by_id",
			return_value=mock_article,
		),
		patch(
			"ai_ticket_platform.routers.articles.ArticleGenerationService"
		) as mock_service_class,
	):
		mock_service = MagicMock()
		mock_service.approve_article = AsyncMock(return_value=approval_result)
		mock_service_class.return_value = mock_service

		result = await approve_article(article_id, mock_db, mock_settings)

		assert result["status"] == "success"
		assert result["article_id"] == article_id
		assert result["intent_id"] == 10
		assert result["version"] == 1
		assert result["new_status"] == "accepted"
		assert "article" in result["approved_types"]


@pytest.mark.asyncio
async def test_approve_article_not_found(mock_db, mock_settings):
	"""Test article approval when article doesn't exist"""
	article_id = 999

	with patch("ai_ticket_platform.routers.articles.get_article_by_id", return_value=None):
		with pytest.raises(HTTPException) as exc_info:
			await approve_article(article_id, mock_db, mock_settings)

		assert exc_info.value.status_code == 404
		assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_approve_article_service_error(mock_db, mock_settings):
	"""Test article approval when service returns error"""
	article_id = 1
	mock_article = MagicMock()

	error_result = {"status": "error", "error": "Approval service failed"}

	with (
		patch(
			"ai_ticket_platform.routers.articles.get_article_by_id",
			return_value=mock_article,
		),
		patch(
			"ai_ticket_platform.routers.articles.ArticleGenerationService"
		) as mock_service_class,
	):
		mock_service = MagicMock()
		mock_service.approve_article = AsyncMock(return_value=error_result)
		mock_service_class.return_value = mock_service

		with pytest.raises(HTTPException) as exc_info:
			await approve_article(article_id, mock_db, mock_settings)

		assert exc_info.value.status_code == 500
		assert "Approval service failed" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_approve_article_unexpected_exception(mock_db, mock_settings):
	"""Test article approval with unexpected exception"""
	article_id = 1
	mock_article = MagicMock()

	with (
		patch(
			"ai_ticket_platform.routers.articles.get_article_by_id",
			return_value=mock_article,
		),
		patch(
			"ai_ticket_platform.routers.articles.ArticleGenerationService"
		) as mock_service_class,
	):
		mock_service_class.side_effect = Exception("Unexpected error")

		with pytest.raises(HTTPException) as exc_info:
			await approve_article(article_id, mock_db, mock_settings)

		assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_iterate_article_success(mock_db, mock_queue):
	"""Test successful article iteration"""
	article_id = 1
	feedback = "Please improve the introduction"
	request = IterateArticleRequest(feedback=feedback)

	mock_article = MagicMock()
	mock_article.id = article_id
	mock_article.intent_id = 10
	mock_article.version = 1

	mock_updated_article = MagicMock()
	mock_updated_article.id = article_id
	mock_updated_article.feedback = feedback

	with (
		patch(
			"ai_ticket_platform.routers.articles.get_article_by_id",
			return_value=mock_article,
		),
		patch(
			"ai_ticket_platform.routers.articles.update_article",
			return_value=mock_updated_article,
		),
	):
		result = await iterate_article(article_id, request, mock_queue, mock_db)

		assert result["status"] == "success"
		assert result["article_id"] == article_id
		assert result["intent_id"] == 10
		assert result["current_version"] == 1
		assert result["next_version"] == 2
		assert result["feedback_saved"] is True
		assert result["job_id"] == "test-job-123"

		# Verify queue.enqueue was called
		mock_queue.enqueue.assert_called_once()


@pytest.mark.asyncio
async def test_iterate_article_not_found(mock_db, mock_queue):
	"""Test article iteration when article doesn't exist"""
	article_id = 999
	request = IterateArticleRequest(feedback="Test feedback")

	with patch("ai_ticket_platform.routers.articles.get_article_by_id", return_value=None):
		with pytest.raises(HTTPException) as exc_info:
			await iterate_article(article_id, request, mock_queue, mock_db)

		assert exc_info.value.status_code == 404
		assert "not found" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_iterate_article_update_fails_after_enqueue(mock_db, mock_queue):
	"""Test iteration when update fails after job is enqueued"""
	article_id = 1
	request = IterateArticleRequest(feedback="Test feedback")

	mock_article = MagicMock()
	mock_article.id = article_id
	mock_article.intent_id = 10
	mock_article.version = 1

	with (
		patch(
			"ai_ticket_platform.routers.articles.get_article_by_id",
			return_value=mock_article,
		),
		patch(
			"ai_ticket_platform.routers.articles.update_article", return_value=None
		),
	):
		with pytest.raises(HTTPException) as exc_info:
			await iterate_article(article_id, request, mock_queue, mock_db)

		assert exc_info.value.status_code == 500
		assert "Generation job queued but failed to save feedback" in str(
			exc_info.value.detail
		)

		# Verify job was still enqueued
		mock_queue.enqueue.assert_called_once()


@pytest.mark.asyncio
async def test_iterate_article_enqueue_exception(mock_db, mock_queue):
	"""Test iteration when queue.enqueue raises exception"""
	article_id = 1
	request = IterateArticleRequest(feedback="Test feedback")

	mock_article = MagicMock()
	mock_article.id = article_id
	mock_article.intent_id = 10
	mock_article.version = 1

	mock_queue.enqueue.side_effect = Exception("Queue connection failed")

	with patch(
		"ai_ticket_platform.routers.articles.get_article_by_id",
		return_value=mock_article,
	):
		with pytest.raises(HTTPException) as exc_info:
			await iterate_article(article_id, request, mock_queue, mock_db)

		assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_iterate_article_with_empty_feedback(mock_db, mock_queue):
	"""Test iteration with empty feedback string"""
	article_id = 1
	request = IterateArticleRequest(feedback="")

	mock_article = MagicMock()
	mock_article.id = article_id
	mock_article.intent_id = 10
	mock_article.version = 1

	mock_updated_article = MagicMock()

	with (
		patch(
			"ai_ticket_platform.routers.articles.get_article_by_id",
			return_value=mock_article,
		),
		patch(
			"ai_ticket_platform.routers.articles.update_article",
			return_value=mock_updated_article,
		),
	):
		result = await iterate_article(article_id, request, mock_queue, mock_db)

		# Should still succeed - empty feedback is valid
		assert result["status"] == "success"
		assert result["feedback_saved"] is True
