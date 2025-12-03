"""Unit tests for external/analytics router endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.routers.external import router


@pytest.mark.asyncio
class TestCollectEvent:
	"""Test POST /external/collect endpoint."""

	async def test_collect_impression_event_variant_a(self):
		"""Test collecting impression event for variant A."""
		mock_db = MagicMock(spec=AsyncSession)

		# External router has 4 routes, collect is index 1
		collect_endpoint = router.routes[1].endpoint

		event_data = MagicMock()
		event_data.type = "impression"
		event_data.intent_id = 1
		event_data.variant = "A"

		with patch("ai_ticket_platform.routers.external.increment_variant_impressions", new=AsyncMock(return_value=True)):
			result = await collect_endpoint(event=event_data, db=mock_db)

			assert result == {"success": True}

	async def test_collect_resolution_event_variant_b(self):
		"""Test collecting resolution event for variant B."""
		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event_data = MagicMock()
		event_data.type = "resolution"
		event_data.intent_id = 1
		event_data.variant = "B"

		with patch("ai_ticket_platform.routers.external.increment_variant_resolutions", new=AsyncMock(return_value=True)):
			result = await collect_endpoint(event=event_data, db=mock_db)

			assert result == {"success": True}

	async def test_collect_ticket_created_event(self):
		"""Test collecting ticket_created event."""
		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event_data = MagicMock()
		event_data.type = "ticket_created"
		event_data.intent_id = 1
		event_data.variant = "A"

		result = await collect_endpoint(event=event_data, db=mock_db)

		assert result == {"success": True}

	async def test_collect_invalid_variant(self):
		"""Test collecting event with invalid variant raises error."""
		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event_data = MagicMock()
		event_data.type = "impression"
		event_data.intent_id = 1
		event_data.variant = "C"

		with pytest.raises(HTTPException) as exc_info:
			await collect_endpoint(event=event_data, db=mock_db)

		assert exc_info.value.status_code == 400
		assert "Invalid variant" in str(exc_info.value.detail)

	async def test_collect_unknown_event_type(self):
		"""Test collecting unknown event type raises error."""
		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event_data = MagicMock()
		event_data.type = "unknown_event"
		event_data.intent_id = 1
		event_data.variant = "A"

		with pytest.raises(HTTPException) as exc_info:
			await collect_endpoint(event=event_data, db=mock_db)

		assert exc_info.value.status_code == 400
		assert "Unknown event type" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestGetAnalyticsTotals:
	"""Test GET /external/analytics/totals endpoint."""

	async def test_get_analytics_totals_success(self):
		"""Test successful retrieval of analytics totals."""
		mock_db = MagicMock(spec=AsyncSession)

		# Analytics totals is index 2
		totals_endpoint = router.routes[2].endpoint

		mock_totals = {
			"variant_a_impressions": 100,
			"variant_b_impressions": 95,
			"variant_a_resolutions": 20,
			"variant_b_resolutions": 25
		}

		with patch("ai_ticket_platform.routers.external.get_ab_testing_totals", new=AsyncMock(return_value=mock_totals)):
			result = await totals_endpoint(db=mock_db)

			assert result["variant_a_impressions"] == 100
			assert result["variant_b_impressions"] == 95
			assert result["variant_a_resolutions"] == 20
			assert result["variant_b_resolutions"] == 25


@pytest.mark.asyncio
class TestGetAnalyticsByIntent:
	"""Test GET /external/analytics/{intent_id} endpoint."""

	async def test_get_analytics_by_intent_success(self):
		"""Test successful retrieval of intent-specific analytics."""
		mock_db = MagicMock(spec=AsyncSession)

		# Analytics by intent is index 3
		analytics_endpoint = router.routes[3].endpoint

		mock_intent = MagicMock()
		mock_intent.variant_a_impressions = 50
		mock_intent.variant_b_impressions = 45
		mock_intent.variant_a_resolutions = 10
		mock_intent.variant_b_resolutions = 12

		with patch("ai_ticket_platform.routers.external.get_intent", new=AsyncMock(return_value=mock_intent)):
			result = await analytics_endpoint(intent_id=1, db=mock_db)

			assert result["variant_a_impressions"] == 50
			assert result["variant_b_impressions"] == 45
			assert result["variant_a_resolutions"] == 10
			assert result["variant_b_resolutions"] == 12

	async def test_get_analytics_by_intent_not_found(self):
		"""Test analytics for non-existent intent raises 404."""
		mock_db = MagicMock(spec=AsyncSession)

		analytics_endpoint = router.routes[3].endpoint

		with patch("ai_ticket_platform.routers.external.get_intent", new=AsyncMock(return_value=None)):
			with pytest.raises(HTTPException) as exc_info:
				await analytics_endpoint(intent_id=999, db=mock_db)

			assert exc_info.value.status_code == 404
			assert "Intent not found" in str(exc_info.value.detail)
