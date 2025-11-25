import pytest
import sys
from pathlib import Path
from unittest.mock import Mock

# Add source to path to allow direct imports without package __init__.py
backend_src = Path(__file__).resolve().parents[4] / "src"
sys.path.insert(0, str(backend_src))

from ai_ticket_platform.services.clustering.prompt_builder import (
	build_batch_clustering_prompt,
	get_batch_clustering_schema,
	get_task_config,
)


class TestPromptBuilder:
	"""Test suite for prompt_builder module."""

	@pytest.fixture
	def sample_tickets(self):
		"""Create sample ticket objects."""
		tickets = []
		for i in range(3):
			ticket = Mock()
			ticket.subject = f"Subject {i}"
			ticket.body = f"Body {i}"
			tickets.append(ticket)
		return tickets

	@pytest.fixture
	def sample_existing_intents(self):
		"""Create sample existing intents."""
		return [
			{
				"intent_id": 1,
				"category_l1_name": "Authentication",
				"category_l2_name": "Password",
				"category_l3_name": "Reset",
			},
			{
				"intent_id": 2,
				"category_l1_name": "Billing",
				"category_l2_name": "Invoices",
				"category_l3_name": "Download",
			},
		]

	def test_build_batch_clustering_prompt_with_intents(
		self, sample_tickets, sample_existing_intents
	):
		"""Test prompt building with existing intents."""
		prompt = build_batch_clustering_prompt(sample_tickets, sample_existing_intents)

		# Verify existing intents are included
		assert "ID: 1" in prompt
		assert "Authentication > Password > Reset" in prompt
		assert "Billing > Invoices > Download" in prompt

		# Verify tickets are formatted with indices
		assert "[0]" in prompt
		assert "Subject 0" in prompt
		assert "[2]" in prompt
		assert "Subject 2" in prompt

		# Verify batch size mentioned
		assert "3 tickets" in prompt

	def test_build_batch_clustering_prompt_no_existing_intents(self, sample_tickets):
		"""Test prompt building with no existing intents."""
		prompt = build_batch_clustering_prompt(sample_tickets, [])

		assert "NO existing intents" in prompt
		assert "MUST create NEW intents" in prompt

	def test_build_batch_clustering_prompt_truncates_long_body(self):
		"""Test that long ticket bodies are truncated."""
		ticket = Mock()
		ticket.subject = "Test"
		ticket.body = "a" * 300

		prompt = build_batch_clustering_prompt([ticket], [])

		assert "..." in prompt
		assert "a" * 201 not in prompt

	def test_get_batch_clustering_schema_structure(self):
		"""Test schema has correct structure."""
		schema = get_batch_clustering_schema()

		assert schema["type"] == "object"
		assert "assignments" in schema["properties"]
		assert schema["properties"]["assignments"]["type"] == "array"

		item_schema = schema["properties"]["assignments"]["items"]
		assert "ticket_index" in item_schema["properties"]
		assert "decision" in item_schema["properties"]
		assert item_schema["properties"]["decision"]["enum"] == [
			"match_existing",
			"create_new",
		]

	def test_get_batch_clustering_schema_required_fields(self):
		"""Test schema has correct required fields."""
		schema = get_batch_clustering_schema()

		required = schema["properties"]["assignments"]["items"]["required"]
		assert "ticket_index" in required
		assert "decision" in required
		assert "intent_id" in required
		assert "category_l1_name" in required
		assert "category_l2_name" in required
		assert "category_l3_name" in required
		assert "intent_name" in required

	def test_get_task_config(self):
		"""Test task config structure."""
		config = get_task_config()

		assert "system_prompt" in config
		assert "schema_name" in config
		assert config["schema_name"] == "batch_clustering"
		assert "categorizing support tickets" in config["system_prompt"]
