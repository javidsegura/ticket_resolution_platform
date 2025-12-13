"""Unit tests for external router endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from ai_ticket_platform.routers.external import router


@pytest.mark.asyncio
class TestGetExternal:
	"""Test GET /external/ endpoint."""

	async def test_get_external_success(self):
		"""Test successful retrieval of external API message."""
		get_external_endpoint = router.routes[0].endpoint

		result = await get_external_endpoint()

		assert result == {"message": "External API"}


@pytest.mark.asyncio
class TestCollectEvent:
	"""Test POST /external/collect endpoint."""

	async def test_collect_impression_variant_a(self):
		"""Test collecting impression event for variant A."""
		from ai_ticket_platform.routers.external import CollectEvent

		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event = CollectEvent(type="impression", intent_id=1, variant="A")

		with patch(
			"ai_ticket_platform.routers.external.increment_variant_impressions",
			new=AsyncMock(),
		) as mock_increment:
			result = await collect_endpoint(event=event, db=mock_db)

			mock_increment.assert_called_once_with(mock_db, 1, "A")
			assert result == {"success": True}

	async def test_collect_impression_variant_b(self):
		"""Test collecting impression event for variant B."""
		from ai_ticket_platform.routers.external import CollectEvent

		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event = CollectEvent(type="impression", intent_id=2, variant="B")

		with patch(
			"ai_ticket_platform.routers.external.increment_variant_impressions",
			new=AsyncMock(),
		) as mock_increment:
			result = await collect_endpoint(event=event, db=mock_db)

			mock_increment.assert_called_once_with(mock_db, 2, "B")
			assert result == {"success": True}

	async def test_collect_resolution_variant_a(self):
		"""Test collecting resolution event for variant A."""
		from ai_ticket_platform.routers.external import CollectEvent

		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event = CollectEvent(type="resolution", intent_id=3, variant="A")

		with patch(
			"ai_ticket_platform.routers.external.increment_variant_resolutions",
			new=AsyncMock(),
		) as mock_increment:
			result = await collect_endpoint(event=event, db=mock_db)

			mock_increment.assert_called_once_with(mock_db, 3, "A")
			assert result == {"success": True}

	async def test_collect_resolution_variant_b(self):
		"""Test collecting resolution event for variant B."""
		from ai_ticket_platform.routers.external import CollectEvent

		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event = CollectEvent(type="resolution", intent_id=4, variant="B")

		with patch(
			"ai_ticket_platform.routers.external.increment_variant_resolutions",
			new=AsyncMock(),
		) as mock_increment:
			result = await collect_endpoint(event=event, db=mock_db)

			mock_increment.assert_called_once_with(mock_db, 4, "B")
			assert result == {"success": True}

	async def test_collect_ticket_created(self):
		"""Test collecting ticket_created event."""
		from ai_ticket_platform.routers.external import CollectEvent

		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event = CollectEvent(type="ticket_created", intent_id=5, variant="A")

		result = await collect_endpoint(event=event, db=mock_db)

		assert result == {"success": True}

	async def test_collect_invalid_variant(self):
		"""Test collecting event with invalid variant."""
		from ai_ticket_platform.routers.external import CollectEvent

		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event = CollectEvent(type="impression", intent_id=1, variant="C")

		with pytest.raises(HTTPException) as exc_info:
			await collect_endpoint(event=event, db=mock_db)

		assert exc_info.value.status_code == 400
		assert "Invalid variant" in str(exc_info.value.detail)

	async def test_collect_unknown_event_type(self):
		"""Test collecting event with unknown type."""
		from ai_ticket_platform.routers.external import CollectEvent

		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = router.routes[1].endpoint

		event = CollectEvent(type="unknown_type", intent_id=1, variant="A")

		with pytest.raises(HTTPException) as exc_info:
			await collect_endpoint(event=event, db=mock_db)

		assert exc_info.value.status_code == 400
		assert "Unknown event type" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestGetAnalyticsTotals:
	"""Test GET /external/analytics/totals endpoint."""

	async def test_get_analytics_totals_success(self):
		"""Test successful retrieval of analytics totals."""
		mock_db = MagicMock(spec=AsyncSession)

		get_totals_endpoint = router.routes[2].endpoint

		mock_totals = {
			"variant_a_impressions": 1000,
			"variant_b_impressions": 950,
			"variant_a_resolutions": 250,
			"variant_b_resolutions": 230,
		}

		with patch(
			"ai_ticket_platform.routers.external.get_ab_testing_totals",
			new=AsyncMock(return_value=mock_totals),
		):
			result = await get_totals_endpoint(db=mock_db)

			assert result == mock_totals
			assert result["variant_a_impressions"] == 1000
			assert result["variant_b_impressions"] == 950


@pytest.mark.asyncio
class TestGetAnalyticsByIntent:
	"""Test GET /external/analytics/{intent_id} endpoint."""

	async def test_get_analytics_by_intent_success(self):
		"""Test successful retrieval of analytics for specific intent."""
		mock_db = MagicMock(spec=AsyncSession)

		get_analytics_endpoint = router.routes[3].endpoint

		mock_intent = MagicMock()
		mock_intent.variant_a_impressions = 100
		mock_intent.variant_b_impressions = 95
		mock_intent.variant_a_resolutions = 25
		mock_intent.variant_b_resolutions = 22

		with patch(
			"ai_ticket_platform.routers.external.get_intent",
			new=AsyncMock(return_value=mock_intent),
		):
			result = await get_analytics_endpoint(intent_id=1, db=mock_db)

			assert result["variant_a_impressions"] == 100
			assert result["variant_b_impressions"] == 95
			assert result["variant_a_resolutions"] == 25
			assert result["variant_b_resolutions"] == 22

	async def test_get_analytics_by_intent_not_found(self):
		"""Test retrieving analytics for non-existent intent."""
		mock_db = MagicMock(spec=AsyncSession)

		get_analytics_endpoint = router.routes[3].endpoint

		with patch(
			"ai_ticket_platform.routers.external.get_intent",
			new=AsyncMock(return_value=None),
		):
			with pytest.raises(HTTPException) as exc_info:
				await get_analytics_endpoint(intent_id=999, db=mock_db)

			assert exc_info.value.status_code == 404
			assert "Intent not found" in str(exc_info.value.detail)
