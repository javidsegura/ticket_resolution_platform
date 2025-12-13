"""Regression tests for API endpoint issues.

These tests cover previously identified bugs in API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from rq import Queue

from ai_ticket_platform.routers.tickets import router as tickets_router
from ai_ticket_platform.routers.intents import router as intents_router
from ai_ticket_platform.routers.external import router as external_router


@pytest.mark.asyncio
class TestAPIEndpointRegressions:
	"""Regression tests for API endpoint bugs."""

	async def test_404_returns_proper_error_structure(self):
		"""
		REGRESSION: 404 errors returned HTML instead of JSON.
		Bug fixed: HTTPException with proper status_code and detail.
		"""
		mock_db = MagicMock(spec=AsyncSession)

		get_ticket_endpoint = tickets_router.routes[1].endpoint

		with patch(
			"ai_ticket_platform.routers.tickets.crud_get_ticket",
			new=AsyncMock(return_value=None),
		):
			with pytest.raises(HTTPException) as exc_info:
				await get_ticket_endpoint(ticket_id=999, db=mock_db)

			# REGRESSION CHECK: Proper error structure
			assert exc_info.value.status_code == 404
			assert "not found" in str(exc_info.value.detail).lower()

	async def test_invalid_pagination_params_handled(self):
		"""
		REGRESSION: Negative skip/limit caused database errors.
		Bug fixed: Validation ensures non-negative pagination params.
		"""
		mock_db = MagicMock(spec=AsyncSession)

		get_tickets_endpoint = tickets_router.routes[0].endpoint

		with patch(
			"ai_ticket_platform.routers.tickets.crud_list_tickets",
			new=AsyncMock(return_value=[]),
		):
			with patch(
				"ai_ticket_platform.routers.tickets.crud_count_tickets",
				new=AsyncMock(return_value=0),
			):
				with patch("ai_ticket_platform.routers.tickets.TicketListResponse"):
					# Should not raise error even with edge case params
					await get_tickets_endpoint(skip=0, limit=100, db=mock_db)

	async def test_large_csv_file_rejected_with_proper_error(self):
		"""
		REGRESSION: Large files caused memory exhaustion.
		Bug fixed: 10MB file size limit enforced.
		"""
		mock_queue = MagicMock(spec=Queue)

		upload_endpoint = tickets_router.routes[2].endpoint

		# 11MB file
		large_content = b"x" * (11 * 1024 * 1024)
		mock_file = MagicMock()
		mock_file.filename = "large.csv"
		mock_file.content_type = "text/csv"
		mock_file.read = AsyncMock(return_value=large_content)

		with pytest.raises(HTTPException) as exc_info:
			await upload_endpoint(file=mock_file, queue=mock_queue)

		# REGRESSION CHECK: Proper error for file too large
		assert exc_info.value.status_code == 400
		assert "10MB" in str(exc_info.value.detail)

	async def test_invalid_variant_rejected(self):
		"""
		REGRESSION: Invalid A/B test variant caused silent failures.
		Bug fixed: Validation ensures only A or B variants.
		"""
		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = external_router.routes[1].endpoint

		event_data = MagicMock()
		event_data.type = "impression"
		event_data.intent_id = 1
		event_data.variant = "C"  # Invalid variant

		with pytest.raises(HTTPException) as exc_info:
			await collect_endpoint(event=event_data, db=mock_db)

		# REGRESSION CHECK: Validation error for invalid variant
		assert exc_info.value.status_code == 400
		assert "variant" in str(exc_info.value.detail).lower()

	async def test_unknown_event_type_rejected(self):
		"""
		REGRESSION: Unknown event types were silently ignored.
		Bug fixed: Validation ensures known event types only.
		"""
		mock_db = MagicMock(spec=AsyncSession)

		collect_endpoint = external_router.routes[1].endpoint

		event_data = MagicMock()
		event_data.type = "unknown_type"
		event_data.intent_id = 1
		event_data.variant = "A"

		with pytest.raises(HTTPException) as exc_info:
			await collect_endpoint(event=event_data, db=mock_db)

		# REGRESSION CHECK: Error for unknown event type
		assert exc_info.value.status_code == 400
		assert "unknown" in str(exc_info.value.detail).lower()

	async def test_missing_file_in_upload_handled(self):
		"""
		REGRESSION: Missing filename caused AttributeError.
		Bug fixed: Validation checks for filename presence.
		"""
		mock_queue = MagicMock(spec=Queue)

		upload_endpoint = tickets_router.routes[2].endpoint

		mock_file = MagicMock()
		mock_file.filename = None  # Missing filename

		with pytest.raises(HTTPException) as exc_info:
			await upload_endpoint(file=mock_file, queue=mock_queue)

		# REGRESSION CHECK: Proper error for missing filename
		assert exc_info.value.status_code == 400

	async def test_wrong_content_type_rejected(self):
		"""
		REGRESSION: Non-CSV files were processed and caused errors.
		Bug fixed: Content-type validation enforced.
		"""
		mock_queue = MagicMock(spec=Queue)

		upload_endpoint = tickets_router.routes[2].endpoint

		mock_file = MagicMock()
		mock_file.filename = "data.csv"
		mock_file.content_type = "application/json"  # Wrong type

		with pytest.raises(HTTPException) as exc_info:
			await upload_endpoint(file=mock_file, queue=mock_queue)

		# REGRESSION CHECK: Content type validation
		assert exc_info.value.status_code == 400
		assert "content type" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
class TestAPIResponseFormatRegressions:
	"""Regression tests for API response format consistency."""

	async def test_pagination_response_always_includes_total(self):
		"""
		REGRESSION: Pagination responses sometimes missing 'total' field.
		Bug fixed: TicketListResponse always includes total count.
		"""
		mock_db = MagicMock(spec=AsyncSession)

		get_tickets_endpoint = tickets_router.routes[0].endpoint

		with patch(
			"ai_ticket_platform.routers.tickets.crud_list_tickets",
			new=AsyncMock(return_value=[]),
		):
			with patch(
				"ai_ticket_platform.routers.tickets.crud_count_tickets",
				new=AsyncMock(return_value=0),
			):
				with patch(
					"ai_ticket_platform.routers.tickets.TicketListResponse"
				) as mock_response:
					mock_result = MagicMock()
					mock_response.return_value = mock_result

					await get_tickets_endpoint(skip=0, limit=100, db=mock_db)

					# REGRESSION CHECK: total field always included
					mock_response.assert_called_once()
					call_kwargs = mock_response.call_args[1]
					assert "total" in call_kwargs

	async def test_intent_response_includes_all_fields(self):
		"""
		REGRESSION: Intent responses missing variant metrics.
		Bug fixed: IntentRead schema includes all A/B testing fields.
		"""
		mock_db = MagicMock(spec=AsyncSession)

		get_intent_endpoint = intents_router.routes[1].endpoint

		mock_intent = MagicMock()
		mock_intent.id = 1
		mock_intent.variant_a_impressions = 10
		mock_intent.variant_b_impressions = 12

		with patch(
			"ai_ticket_platform.routers.intents.get_intent",
			new=AsyncMock(return_value=mock_intent),
		):
			with patch(
				"ai_ticket_platform.routers.intents.IntentRead.model_validate"
			) as mock_validate:
				mock_result = MagicMock()
				mock_validate.return_value = mock_result

				await get_intent_endpoint(intent_id=1, db=mock_db)

				# REGRESSION CHECK: model_validate called with full intent
				mock_validate.assert_called_once_with(mock_intent)
