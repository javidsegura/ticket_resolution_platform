import pytest
from unittest.mock import Mock, AsyncMock, patch
from ai_ticket_platform.services.clustering.cluster_service import cluster_tickets


class TestClusterService:
	"""Test suite for cluster_service module."""

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
		for i in range(5):
			ticket = Mock()
			ticket.id = i + 1
			ticket.subject = f"Test ticket {i + 1}"
			ticket.body = f"Body of test ticket {i + 1}"
			tickets.append(ticket)
		return tickets

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
	async def test_cluster_tickets_single_batch(
		self, mock_db, mock_llm_client, sample_tickets
	):
		"""Test clustering with single batch of tickets."""
		with patch(
			"ai_ticket_platform.services.clustering.cluster_service.intent_crud.get_all_intents_with_categories"
		) as mock_get_intents, patch(
			"ai_ticket_platform.services.clustering.cluster_service.batch_processor.process_batch"
		) as mock_process_batch:
			mock_get_intents.return_value = []
			mock_process_batch.return_value = [
				{
					"ticket_id": i + 1,
					"intent_id": 1,
					"intent_name": "Test Intent",
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

			result = await cluster_tickets(
				mock_db, mock_llm_client, sample_tickets, batch_size=10
			)

			assert result["total_tickets"] == 5
			assert len(result["assignments"]) == 5
			mock_process_batch.assert_called_once()

	@pytest.mark.asyncio
	async def test_cluster_tickets_multiple_batches(
		self, mock_db, mock_llm_client, sample_tickets
	):
		"""Test clustering processes multiple batches correctly."""
		with patch(
			"ai_ticket_platform.services.clustering.cluster_service.intent_crud.get_all_intents_with_categories"
		) as mock_get_intents, patch(
			"ai_ticket_platform.services.clustering.cluster_service.batch_processor.process_batch"
		) as mock_process_batch:
			mock_get_intents.return_value = []
			# Return correct number of assignments per batch (2, 2, 1)
			mock_process_batch.side_effect = [
				[
					{
						"ticket_id": 1,
						"decision": "create_new",
						"is_new_intent": True,
						"intent_id": 1,
						"intent_name": "Test Intent 1",
						"category_l1_id": 1,
						"category_l1_name": "L1",
						"category_l2_id": 2,
						"category_l2_name": "L2",
						"category_l3_id": 3,
						"category_l3_name": "L3",
					},
					{
						"ticket_id": 2,
						"decision": "create_new",
						"is_new_intent": True,
						"intent_id": 2,
						"intent_name": "Test Intent 2",
						"category_l1_id": 1,
						"category_l1_name": "L1",
						"category_l2_id": 2,
						"category_l2_name": "L2",
						"category_l3_id": 3,
						"category_l3_name": "L3",
					}
				],
				[
					{
						"ticket_id": 3,
						"decision": "create_new",
						"is_new_intent": True,
						"intent_id": 3,
						"intent_name": "Test Intent 3",
						"category_l1_id": 1,
						"category_l1_name": "L1",
						"category_l2_id": 2,
						"category_l2_name": "L2",
						"category_l3_id": 3,
						"category_l3_name": "L3",
					},
					{
						"ticket_id": 4,
						"decision": "create_new",
						"is_new_intent": True,
						"intent_id": 4,
						"intent_name": "Test Intent 4",
						"category_l1_id": 1,
						"category_l1_name": "L1",
						"category_l2_id": 2,
						"category_l2_name": "L2",
						"category_l3_id": 3,
						"category_l3_name": "L3",
					}
				],
				[
					{
						"ticket_id": 5,
						"decision": "create_new",
						"is_new_intent": True,
						"intent_id": 5,
						"intent_name": "Test Intent 5",
						"category_l1_id": 1,
						"category_l1_name": "L1",
						"category_l2_id": 2,
						"category_l2_name": "L2",
						"category_l3_id": 3,
						"category_l3_name": "L3",
					}
				]
			]

			# Process 5 tickets with batch_size=2 should result in 3 batches
			result = await cluster_tickets(
				mock_db, mock_llm_client, sample_tickets, batch_size=2
			)

			assert mock_process_batch.call_count == 3
			assert result["total_tickets"] == 5

	@pytest.mark.asyncio
	async def test_cluster_tickets_updates_existing_intents(
		self, mock_db, mock_llm_client, sample_tickets
	):
		"""Test that newly created intents are added to existing_intents for subsequent batches."""
		with patch(
			"ai_ticket_platform.services.clustering.cluster_service.intent_crud.get_all_intents_with_categories"
		) as mock_get_intents, patch(
			"ai_ticket_platform.services.clustering.cluster_service.batch_processor.process_batch"
		) as mock_process_batch:
			mock_get_intents.return_value = []

			# First batch creates a new intent
			mock_process_batch.side_effect = [
				[
					{
						"ticket_id": 1,
						"decision": "create_new",
						"is_new_intent": True,
						"intent_id": 100,
						"intent_name": "New Intent",
						"category_l1_id": 1,
						"category_l1_name": "L1",
						"category_l2_id": 2,
						"category_l2_name": "L2",
						"category_l3_id": 3,
						"category_l3_name": "L3",
					}
				],
				[{"ticket_id": 2, "decision": "match_existing", "is_new_intent": False}],
			]

			await cluster_tickets(
				mock_db, mock_llm_client, sample_tickets[:2], batch_size=1
			)

			# Verify second batch received the newly created intent
			second_call_kwargs = mock_process_batch.call_args_list[1][1]
			assert len(second_call_kwargs["existing_intents"]) == 1
			assert second_call_kwargs["existing_intents"][0]["intent_id"] == 100
