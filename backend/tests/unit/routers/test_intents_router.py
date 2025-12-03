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
		mock_intent_2 = MagicMock()

		# Intents router has 2 routes: list (index 0) and get by id (index 1)
		get_intents_endpoint = router.routes[0].endpoint

		mock_result_1 = MagicMock()
		mock_result_1.id = 1
		mock_result_2 = MagicMock()
		mock_result_2.id = 2

		with patch("ai_ticket_platform.routers.intents.list_intents", new=AsyncMock(return_value=[mock_intent_1, mock_intent_2])):
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

		get_intents_endpoint = router.routes[0].endpoint

		mock_result = MagicMock()
		mock_result.is_processed = True

		with patch("ai_ticket_platform.routers.intents.list_intents", new=AsyncMock(return_value=[mock_intent])):
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
