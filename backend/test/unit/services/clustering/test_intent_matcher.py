import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta
from ai_ticket_platform.services.clustering.intent_matcher import (
	process_match_decision,
	process_create_decision,
	_is_newly_created,
)


class TestIntentMatcher:
	"""Test suite for intent_matcher module."""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session."""
		return AsyncMock()

	@pytest.fixture
	def sample_ticket(self):
		"""Create sample ticket."""
		ticket = Mock()
		ticket.id = 1
		ticket.subject = "Test subject"
		ticket.body = "Test body"
		return ticket

	@pytest.fixture
	def sample_existing_intents(self):
		"""Create sample existing intents."""
		return [
			{
				"intent_id": 100,
				"intent_name": "Existing Intent",
				"category_l1_id": 1,
				"category_l1_name": "Auth",
				"category_l2_id": 2,
				"category_l2_name": "Password",
				"category_l3_id": 3,
				"category_l3_name": "Reset",
			}
		]

	@pytest.mark.asyncio
	async def test_process_match_decision_success(
		self, mock_db, sample_ticket, sample_existing_intents
	):
		"""Test successful match to existing intent."""
		llm_result = {
			"intent_id": 100,
			"confidence": 0.95,
			"reasoning": "Exact match",
		}

		with patch(
			"ai_ticket_platform.services.clustering.intent_matcher.intent_crud.update_ticket_intent"
		) as mock_update:
			result = await process_match_decision(
				mock_db, sample_ticket, llm_result, sample_existing_intents
			)

			mock_update.assert_called_once_with(mock_db, 1, 100)
			assert result["decision"] == "match_existing"
			assert result["intent_id"] == 100
			assert result["is_new_intent"] is False
			assert result["category_l1_name"] == "Auth"

	@pytest.mark.asyncio
	async def test_process_match_decision_missing_intent_id(
		self, mock_db, sample_ticket, sample_existing_intents
	):
		"""Test match decision with missing intent_id raises error."""
		llm_result = {"intent_id": None}

		with pytest.raises(ValueError, match="didn't provide intent_id"):
			await process_match_decision(
				mock_db, sample_ticket, llm_result, sample_existing_intents
			)

	@pytest.mark.asyncio
	async def test_process_match_decision_nonexistent_intent(
		self, mock_db, sample_ticket, sample_existing_intents
	):
		"""Test match decision with non-existent intent_id raises error."""
		llm_result = {"intent_id": 999}

		with pytest.raises(ValueError, match="non-existent intent ID"):
			await process_match_decision(
				mock_db, sample_ticket, llm_result, sample_existing_intents
			)

	@pytest.mark.asyncio
	async def test_process_create_decision_success(self, mock_db, sample_ticket):
		"""Test successful creation of new intent."""
		llm_result = {
			"category_l1_name": "New L1",
			"category_l2_name": "New L2",
			"category_l3_name": "New L3",
			"intent_name": "New Intent Name",
			"confidence": 0.9,
			"reasoning": "Unique issue",
		}

		stats = {"intents_created": 0, "intents_matched": 0, "categories_created": {"l1": 0, "l2": 0, "l3": 0}}

		with patch(
			"ai_ticket_platform.services.clustering.intent_matcher.category_crud.get_or_create_category"
		) as mock_get_category, patch(
			"ai_ticket_platform.services.clustering.intent_matcher.intent_crud.get_or_create_intent"
		) as mock_get_intent, patch(
			"ai_ticket_platform.services.clustering.intent_matcher.intent_crud.update_ticket_intent"
		) as mock_update, patch(
			"ai_ticket_platform.services.clustering.intent_matcher._is_newly_created"
		) as mock_is_new:
			# Mock newly created categories and intent
			mock_l1 = Mock()
			mock_l1.id = 1
			mock_l1.created_at = datetime.now(timezone.utc)

			mock_l2 = Mock()
			mock_l2.id = 2
			mock_l2.created_at = datetime.now(timezone.utc)

			mock_l3 = Mock()
			mock_l3.id = 3
			mock_l3.created_at = datetime.now(timezone.utc)

			mock_intent = Mock()
			mock_intent.id = 100
			mock_intent.created_at = datetime.now(timezone.utc)

			mock_get_category.side_effect = [mock_l1, mock_l2, mock_l3]
			mock_get_intent.return_value = mock_intent
			mock_is_new.return_value = True

			result = await process_create_decision(mock_db, sample_ticket, llm_result, stats)

			assert mock_get_category.call_count == 3
			assert result["decision"] == "create_new"
			assert result["intent_name"] == "New Intent Name"
			assert result["is_new_intent"] is True
			assert stats["intents_created"] == 1
			assert stats["categories_created"]["l1"] == 1
			assert stats["categories_created"]["l2"] == 1
			assert stats["categories_created"]["l3"] == 1

	@pytest.mark.asyncio
	async def test_process_create_decision_missing_category_names(
		self, mock_db, sample_ticket
	):
		"""Test create decision with missing category names raises error."""
		llm_result = {
			"category_l1_name": "L1",
			"category_l2_name": None,
			"category_l3_name": "L3",
			"intent_name": "Intent",
		}

		stats = {"intents_created": 0, "intents_matched": 0, "categories_created": {"l1": 0, "l2": 0, "l3": 0}}

		with pytest.raises(ValueError, match="didn't provide all 3 category names"):
			await process_create_decision(mock_db, sample_ticket, llm_result, stats)

	@pytest.mark.asyncio
	async def test_process_create_decision_missing_intent_name(
		self, mock_db, sample_ticket
	):
		"""Test create decision with missing intent name raises error."""
		llm_result = {
			"category_l1_name": "L1",
			"category_l2_name": "L2",
			"category_l3_name": "L3",
			"intent_name": None,
		}

		stats = {"intents_created": 0, "intents_matched": 0, "categories_created": {"l1": 0, "l2": 0, "l3": 0}}

		with pytest.raises(ValueError, match="didn't provide intent_name"):
			await process_create_decision(mock_db, sample_ticket, llm_result, stats)

	@pytest.mark.asyncio
	async def test_is_newly_created_true(self):
		"""Test _is_newly_created returns True for recent objects."""
		obj = Mock()
		obj.created_at = datetime.now(timezone.utc)

		assert await _is_newly_created(obj) is True

	@pytest.mark.asyncio
	async def test_is_newly_created_false(self):
		"""Test _is_newly_created returns False for old objects."""
		obj = Mock()
		obj.created_at = datetime.now(timezone.utc) - timedelta(seconds=10)

		assert await _is_newly_created(obj) is False

	@pytest.mark.asyncio
	async def test_is_newly_created_no_attribute(self):
		"""Test _is_newly_created returns False for objects without created_at."""
		obj = Mock(spec=[])

		assert await _is_newly_created(obj) is False
