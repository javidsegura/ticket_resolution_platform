import pytest
from unittest.mock import Mock, AsyncMock, patch
from ai_ticket_platform.services.clustering.cluster_interface import cluster_tickets


class TestClusterService:
	"""Test suite for cluster_interface module."""

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session."""
		return AsyncMock()

	@pytest.fixture
	def mock_llm_client(self):
		"""Create mock LLM client."""
		mock = Mock()
		mock.call_llm_structured = Mock()
		return mock

	@pytest.fixture
	def sample_tickets(self):
		"""Create sample ticket dictionaries."""
		return [
			{"id": i + 1, "subject": f"Test ticket {i + 1}", "body": f"Body of test ticket {i + 1}"}
			for i in range(5)
		]

	@pytest.mark.asyncio
	async def test_cluster_tickets_empty_list(self, mock_db, mock_llm_client):
		"""Test clustering with empty ticket list."""
		result = await cluster_tickets(mock_db, mock_llm_client, [])

		assert result["total_tickets"] == 0
		assert result["intents_created"] == 0
		assert result["intents_matched"] == 0
		assert result["categories_created"]["l1"] == 0
		assert result["categories_created"]["l2"] == 0
		assert result["categories_created"]["l3"] == 0
		assert result["assignments"] == []

	@pytest.mark.asyncio
	async def test_cluster_tickets_processes_batch(
		self, mock_db, mock_llm_client, sample_tickets
	):
		"""Test clustering processes all tickets in a single batch."""
		with patch(
			"ai_ticket_platform.services.clustering.cluster_interface.intent_crud.get_all_intents_with_categories"
		) as mock_get_intents, patch(
			"ai_ticket_platform.services.clustering.cluster_interface.intent_matcher.process_create_decision"
		) as mock_process_create, patch(
			"asyncio.to_thread"
		) as mock_to_thread:
			mock_get_intents.return_value = []

			# Mock LLM response
			mock_to_thread.return_value = {
				"assignments": [
					{
						"ticket_index": i,
						"decision": "create_new",
						"category_l1_name": "L1",
						"category_l2_name": "L2",
						"category_l3_name": "L3",
						"intent_name": f"Test Intent {i+1}",
						"confidence": 0.9,
						"reasoning": "Test"
					}
					for i in range(5)
				]
			}

			# Mock process_create_decision for each ticket
			mock_process_create.side_effect = [
				{
					"ticket_id": i + 1,
					"intent_id": i + 1,
					"intent_name": f"Test Intent {i+1}",
					"decision": "create_new",
					"is_new_intent": True,
					"category_l1_id": 1,
					"category_l1_name": "L1",
					"category_l2_id": 2,
					"category_l2_name": "L2",
					"category_l3_id": 3,
					"category_l3_name": "L3",
				}
				for i in range(5)
			]

			result = await cluster_tickets(mock_db, mock_llm_client, sample_tickets)

			assert result["total_tickets"] == 5
			assert len(result["assignments"]) == 5
			mock_to_thread.assert_called_once()

	@pytest.mark.asyncio
	async def test_cluster_tickets_match_existing(
		self, mock_db, mock_llm_client, sample_tickets
	):
		"""Test clustering can match tickets to existing intents."""
		with patch(
			"ai_ticket_platform.services.clustering.cluster_interface.intent_crud.get_all_intents_with_categories"
		) as mock_get_intents, patch(
			"ai_ticket_platform.services.clustering.cluster_interface.intent_matcher.process_match_decision"
		) as mock_process_match, patch(
			"asyncio.to_thread"
		) as mock_to_thread:
			# Return existing intents
			mock_get_intents.return_value = [
				{
					"intent_id": 100,
					"intent_name": "Existing Intent",
					"category_l1_id": 1,
					"category_l1_name": "L1",
					"category_l2_id": 2,
					"category_l2_name": "L2",
					"category_l3_id": 3,
					"category_l3_name": "L3",
				}
			]

			# Mock LLM to match all tickets to existing intent
			mock_to_thread.return_value = {
				"assignments": [
					{
						"ticket_index": i,
						"decision": "match_existing",
						"intent_id": 100,
						"confidence": 0.9,
						"reasoning": "Test"
					}
					for i in range(5)
				]
			}

			# Mock process_match_decision
			mock_process_match.side_effect = [
				{
					"ticket_id": i + 1,
					"intent_id": 100,
					"intent_name": "Existing Intent",
					"decision": "match_existing",
					"is_new_intent": False,
					"category_l1_id": 1,
					"category_l1_name": "L1",
					"category_l2_id": 2,
					"category_l2_name": "L2",
					"category_l3_id": 3,
					"category_l3_name": "L3",
				}
				for i in range(5)
			]

			result = await cluster_tickets(mock_db, mock_llm_client, sample_tickets)

			assert result["total_tickets"] == 5
			assert result["intents_matched"] == 5
			assert result["intents_created"] == 0
