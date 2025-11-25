import pytest
from unittest.mock import Mock, AsyncMock, patch
from ai_ticket_platform.services.clustering.batch_processor import process_batch


class TestBatchProcessor:
	"""Test suite for batch_processor module."""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session."""
		return AsyncMock()

	@pytest.fixture
	def mock_llm_client(self):
		"""Create mock LLM client."""
		return Mock()

	@pytest.fixture
	def sample_tickets(self):
		"""Create sample ticket objects."""
		tickets = []
		for i in range(3):
			ticket = Mock()
			ticket.id = i + 1
			ticket.subject = f"Test ticket {i + 1}"
			ticket.body = f"Body {i + 1}"
			tickets.append(ticket)
		return tickets

	@pytest.fixture
	def sample_existing_intents(self):
		"""Create sample existing intents."""
		return [
			{
				"intent_id": 1,
				"intent_name": "Existing Intent",
				"category_l1_id": 1,
				"category_l1_name": "Authentication",
				"category_l2_id": 2,
				"category_l2_name": "Password",
				"category_l3_id": 3,
				"category_l3_name": "Reset",
			}
		]

	@pytest.mark.asyncio
	async def test_process_batch_success(
		self, mock_db, mock_llm_client, sample_tickets, sample_existing_intents
	):
		"""Test successful batch processing."""
		stats = {"intents_created": 0, "intents_matched": 0, "categories_created": {"l1": 0, "l2": 0, "l3": 0}}

		llm_response = {
			"assignments": [
				{
					"ticket_index": 0,
					"decision": "match_existing",
					"intent_id": 1,
					"category_l1_name": None,
					"category_l2_name": None,
					"category_l3_name": None,
					"intent_name": None,
					"confidence": 0.95,
					"reasoning": "Exact match",
				},
				{
					"ticket_index": 1,
					"decision": "create_new",
					"intent_id": None,
					"category_l1_name": "New L1",
					"category_l2_name": "New L2",
					"category_l3_name": "New L3",
					"intent_name": "New Intent",
					"confidence": 0.9,
					"reasoning": "New issue",
				},
				{
					"ticket_index": 2,
					"decision": "match_existing",
					"intent_id": 1,
					"category_l1_name": None,
					"category_l2_name": None,
					"category_l3_name": None,
					"intent_name": None,
					"confidence": 0.92,
					"reasoning": "Similar issue",
				},
			]
		}

		mock_llm_client.call_llm_structured.return_value = llm_response

		with patch(
			"ai_ticket_platform.services.clustering.batch_processor.intent_matcher.process_match_decision"
		) as mock_match, patch(
			"ai_ticket_platform.services.clustering.batch_processor.intent_matcher.process_create_decision"
		) as mock_create:
			mock_match.return_value = {"ticket_id": 1, "decision": "match_existing"}
			mock_create.return_value = {"ticket_id": 2, "decision": "create_new"}

			result = await process_batch(
				mock_db, mock_llm_client, sample_tickets, sample_existing_intents, stats
			)

			assert len(result) == 3
			assert mock_match.call_count == 2
			assert mock_create.call_count == 1
			assert stats["intents_matched"] == 2

	@pytest.mark.asyncio
	async def test_process_batch_validates_assignment_count(
		self, mock_db, mock_llm_client, sample_tickets, sample_existing_intents
	):
		"""Test that process_batch validates LLM returns correct number of assignments."""
		stats = {"intents_created": 0, "intents_matched": 0, "categories_created": {"l1": 0, "l2": 0, "l3": 0}}

		# LLM returns wrong number of assignments
		llm_response = {"assignments": [{"ticket_index": 0, "decision": "match_existing", "intent_id": 1}]}

		mock_llm_client.call_llm_structured.return_value = llm_response

		with pytest.raises(ValueError, match="returned 1 assignments, expected 3"):
			await process_batch(
				mock_db, mock_llm_client, sample_tickets, sample_existing_intents, stats
			)

	@pytest.mark.asyncio
	async def test_process_batch_validates_ticket_index(
		self, mock_db, mock_llm_client, sample_tickets, sample_existing_intents
	):
		"""Test that process_batch validates ticket indices."""
		stats = {"intents_created": 0, "intents_matched": 0, "categories_created": {"l1": 0, "l2": 0, "l3": 0}}

		# Invalid ticket index
		llm_response = {
			"assignments": [
				{"ticket_index": 10, "decision": "match_existing", "intent_id": 1},
				{"ticket_index": 1, "decision": "match_existing", "intent_id": 1},
				{"ticket_index": 2, "decision": "match_existing", "intent_id": 1},
			]
		}

		mock_llm_client.call_llm_structured.return_value = llm_response

		with pytest.raises(ValueError, match="Invalid ticket_index 10"):
			await process_batch(
				mock_db, mock_llm_client, sample_tickets, sample_existing_intents, stats
			)

	@pytest.mark.asyncio
	async def test_process_batch_unknown_decision(
		self, mock_db, mock_llm_client, sample_tickets, sample_existing_intents
	):
		"""Test that process_batch rejects unknown decision types."""
		stats = {"intents_created": 0, "intents_matched": 0, "categories_created": {"l1": 0, "l2": 0, "l3": 0}}

		llm_response = {
			"assignments": [
				{"ticket_index": 0, "decision": "unknown_decision", "intent_id": 1},
				{"ticket_index": 1, "decision": "match_existing", "intent_id": 1},
				{"ticket_index": 2, "decision": "match_existing", "intent_id": 1},
			]
		}

		mock_llm_client.call_llm_structured.return_value = llm_response

		with pytest.raises(ValueError, match="Unknown decision type"):
			await process_batch(
				mock_db, mock_llm_client, sample_tickets, sample_existing_intents, stats
			)
