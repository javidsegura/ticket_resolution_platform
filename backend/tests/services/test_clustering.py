"""
Unit tests for clustering service module.

Tests cover ticket clustering, categorization, prompt building, and LLM integration.
"""

import pytest
from unittest.mock import Mock, patch

from ai_ticket_platform.services.clustering.cluster_service import (
	cluster_and_categorize_tickets,
	_extract_ticket_texts
)
from ai_ticket_platform.services.clustering.llm_clusterer import cluster_tickets
from ai_ticket_platform.services.clustering.prompt_builder import (
	build_clustering_prompt,
	get_output_schema
)


class TestClusterService:
	"""Test suite for cluster_service module."""

	@pytest.fixture
	def mock_llm_client(self):
		"""Create mock LLM client."""
		return Mock()

	@pytest.fixture
	def sample_tickets(self):
		"""Create sample ticket data for testing."""
		return [
			{"Ticket Subject": "Cannot reset my password"},
			{"Ticket Subject": "Password reset link expired"},
			{"Ticket Subject": "Login not working"},
			{"Ticket Subject": "App crashes on startup"},
			{"Ticket Subject": "Payment failed"}
		]

	@pytest.fixture
	def sample_clustering_result(self):
		"""Create sample clustering result from LLM."""
		return {
			"clusters": [
				{
					"topic_name": "Password Reset Issues",
					"product": "Authentication System",
					"category": "Account Access",
					"subcategory": "Password Recovery",
					"ticket_indices": [0, 1],
					"summary": "Users unable to reset passwords or links expired"
				},
				{
					"topic_name": "Login Failures",
					"product": "Authentication System",
					"category": "Account Access",
					"subcategory": "Login",
					"ticket_indices": [2],
					"summary": "Users experiencing login failures"
				},
				{
					"topic_name": "App Stability",
					"product": "Mobile App",
					"category": "Performance",
					"subcategory": "Crashes",
					"ticket_indices": [3],
					"summary": "App crashing on startup"
				},
				{
					"topic_name": "Payment Processing",
					"product": "Payment Gateway",
					"category": "Transactions",
					"subcategory": "Failed Payments",
					"ticket_indices": [4],
					"summary": "Payment failures during checkout"
				}
			]
		}

	def test_cluster_and_categorize_tickets_success(
		self,
		mock_llm_client,
		sample_tickets,
		sample_clustering_result
	):
		"""Test successful clustering of tickets."""
		with patch('ai_ticket_platform.services.clustering.cluster_service.llm_clusterer.cluster_tickets') as mock_cluster:
			mock_cluster.return_value = sample_clustering_result

			result = cluster_and_categorize_tickets(sample_tickets, mock_llm_client)

			# verify llm_clusterer was called with correct arguments
			mock_cluster.assert_called_once()
			call_args = mock_cluster.call_args
			assert call_args[1]['llm_client'] == mock_llm_client
			assert len(call_args[1]['ticket_texts']) == 5

			# verify result structure
			assert result == sample_clustering_result
			assert len(result['clusters']) == 4

	def test_cluster_and_categorize_tickets_empty_list(self, mock_llm_client):
		"""Test clustering with empty ticket list."""
		result = cluster_and_categorize_tickets([], mock_llm_client)

		# verify empty result
		assert result == {
			"total_tickets": 0,
			"clusters_created": 0,
			"clusters": []
		}

	def test_cluster_and_categorize_tickets_all_empty_subjects(self, mock_llm_client):
		"""Test clustering with all empty/missing subjects."""
		tickets = [
			{"Ticket Subject": ""},
			{"Ticket Subject": "   "},
			{"Other Field": "No subject"}
		]

		result = cluster_and_categorize_tickets(tickets, mock_llm_client)

		# verify empty result
		assert result == {
			"total_tickets": 0,
			"clusters_created": 0,
			"clusters": []
		}

	def test_extract_ticket_texts_success(self):
		"""Test extracting ticket subjects from ticket dicts."""
		tickets = [
			{"Ticket Subject": "First ticket"},
			{"Ticket Subject": "Second ticket"},
			{"Ticket Subject": "Third ticket"}
		]

		result = _extract_ticket_texts(tickets)

		assert len(result) == 3
		assert result == ["First ticket", "Second ticket", "Third ticket"]

	def test_extract_ticket_texts_with_whitespace(self):
		"""Test extracting ticket texts strips whitespace."""
		tickets = [
			{"Ticket Subject": "  Ticket with spaces  "},
			{"Ticket Subject": "\tTicket with tabs\t"},
			{"Ticket Subject": "Normal ticket"}
		]

		result = _extract_ticket_texts(tickets)

		assert len(result) == 3
		assert result == ["Ticket with spaces", "Ticket with tabs", "Normal ticket"]

class TestLLMClusterer:
	"""Test suite for llm_clusterer module."""

	@pytest.fixture
	def mock_llm_client(self):
		"""Create mock LLM client."""
		mock_client = Mock()
		return mock_client

	@pytest.fixture
	def sample_ticket_texts(self):
		"""Create sample ticket texts."""
		return [
			"Cannot reset password",
			"Password reset link not working",
			"Login page not loading",
			"App crashes when opening"
		]

	@pytest.fixture
	def sample_llm_response(self):
		"""Create sample LLM response."""
		return {
			"clusters": [
				{
					"topic_name": "Password Reset Issues",
					"product": "Auth System",
					"category": "Password",
					"subcategory": "Reset",
					"ticket_indices": [0, 1],
					"summary": "Password reset problems"
				},
				{
					"topic_name": "Login Issues",
					"product": "Auth System",
					"category": "Login",
					"subcategory": "Page Loading",
					"ticket_indices": [2],
					"summary": "Login page not loading"
				},
				{
					"topic_name": "App Crashes",
					"product": "Mobile App",
					"category": "Stability",
					"subcategory": "Crashes",
					"ticket_indices": [3],
					"summary": "App crashing on startup"
				}
			]
		}

	def test_cluster_tickets_success(
		self,
		mock_llm_client,
		sample_ticket_texts,
		sample_llm_response
	):
		"""Test successful ticket clustering via LLM."""
		mock_llm_client.call_llm_structured.return_value = sample_llm_response

		result = cluster_tickets(mock_llm_client, sample_ticket_texts)

		# verify LLM client was called
		mock_llm_client.call_llm_structured.assert_called_once()
		call_args = mock_llm_client.call_llm_structured.call_args

		# verify prompt was built correctly
		assert "4 support tickets" in call_args[1]['prompt']
		assert "Cannot reset password" in call_args[1]['prompt']

		# verify output schema was provided
		assert 'output_schema' in call_args[1]
		assert call_args[1]['output_schema']['type'] == 'object'

		# verify task config
		assert 'task_config' in call_args[1]
		assert 'system_prompt' in call_args[1]['task_config']
		assert 'clustering expert' in call_args[1]['task_config']['system_prompt']
		assert call_args[1]['task_config']['schema_name'] == 'ticket_clustering'

		# verify temperature
		assert call_args[1]['temperature'] == 0.3

		# verify result
		assert result == sample_llm_response
		assert len(result['clusters']) == 3

	def test_cluster_tickets_extracts_clusters(
		self,
		mock_llm_client,
		sample_ticket_texts,
		sample_llm_response
	):
		"""Test cluster_tickets extracts clusters from LLM response."""
		mock_llm_client.call_llm_structured.return_value = sample_llm_response

		result = cluster_tickets(mock_llm_client, sample_ticket_texts)

		# verify clusters are extracted
		assert 'clusters' in result
		assert len(result['clusters']) == 3

	def test_cluster_tickets_empty_clusters_response(self,
		mock_llm_client,
		sample_ticket_texts
	):
		"""Test handling of LLM response with no clusters."""
		mock_llm_client.call_llm_structured.return_value = {"clusters": []}

		result = cluster_tickets(mock_llm_client, sample_ticket_texts)

		assert result == {"clusters": []}

	def test_cluster_tickets_single_ticket(self, mock_llm_client):
		"""Test clustering with single ticket."""
		ticket_texts = ["Single ticket"]
		mock_llm_client.call_llm_structured.return_value = {
			"clusters": [
				{
					"topic_name": "Single Issue",
					"product": "Product",
					"category": "Category",
					"subcategory": "Subcategory",
					"ticket_indices": [0],
					"summary": "Single ticket issue"
				}
			]
		}

		result = cluster_tickets(mock_llm_client, ticket_texts)

		# verify single cluster created
		assert len(result['clusters']) == 1
		assert result['clusters'][0]['ticket_indices'] == [0]

	def test_cluster_tickets_large_batch(self, mock_llm_client):
		"""Test clustering with large batch of tickets."""
		# create 100 tickets
		ticket_texts = [f"Ticket {i}" for i in range(100)]

		# mock response with multiple clusters
		mock_clusters = [
			{
				"topic_name": f"Cluster {i}",
				"product": "Product",
				"category": "Category",
				"subcategory": "Subcategory",
				"ticket_indices": list(range(i*10, (i+1)*10)),
				"summary": f"Cluster {i} summary"
			}
			for i in range(10)
		]
		mock_llm_client.call_llm_structured.return_value = {"clusters": mock_clusters}

		result = cluster_tickets(mock_llm_client, ticket_texts)

		# verify all tickets were sent
		call_args = mock_llm_client.call_llm_structured.call_args
		assert "100 support tickets" in call_args[1]['prompt']

		# verify all clusters returned
		assert len(result['clusters']) == 10


class TestPromptBuilder:
	"""Test suite for prompt_builder module."""

	def test_build_clustering_prompt_structure(self):
		"""Test prompt building creates correct structure."""
		ticket_texts = [
			"Password reset not working",
			"Cannot login",
			"App crashes"
		]

		prompt = build_clustering_prompt(ticket_texts)

		# verify prompt contains all tickets
		assert "0. Password reset not working" in prompt
		assert "1. Cannot login" in prompt
		assert "2. App crashes" in prompt

		# verify prompt contains count
		assert "3 support tickets" in prompt

		# verify prompt contains clustering instructions
		assert "GRANULAR" in prompt
		assert "SPECIFIC" in prompt
		assert "Product" in prompt or "PRODUCT" in prompt
		assert "Category" in prompt or "CATEGORY" in prompt
		assert "Subcategory" in prompt or "SUBCATEGORY" in prompt

	def test_build_clustering_prompt_single_ticket(self):
		"""Test prompt building with single ticket."""
		ticket_texts = ["Single ticket issue"]

		prompt = build_clustering_prompt(ticket_texts)

		assert "0. Single ticket issue" in prompt
		assert "1 support tickets" in prompt

	def test_build_clustering_prompt_large_batch(self):
		"""Test prompt building with large ticket batch."""
		ticket_texts = [f"Ticket number {i}" for i in range(100)]

		prompt = build_clustering_prompt(ticket_texts)

		# verify count
		assert "100 support tickets" in prompt

		# verify first and last tickets
		assert "0. Ticket number 0" in prompt
		assert "99. Ticket number 99" in prompt

	def test_build_clustering_prompt_special_characters(self):
		"""Test prompt building handles special characters in tickets."""
		ticket_texts = [
			"Ticket with \"quotes\"",
			"Ticket with 'apostrophes'",
			"Ticket with\nnewlines",
			"Ticket with\ttabs"
		]

		prompt = build_clustering_prompt(ticket_texts)

		# verify all tickets are included (special chars preserved)
		assert "Ticket with \"quotes\"" in prompt
		assert "Ticket with 'apostrophes'" in prompt
		assert "newlines" in prompt
		assert "tabs" in prompt

	def test_get_output_schema_structure(self):
		"""Test output schema has correct structure."""
		schema = get_output_schema()

		# verify top level structure
		assert schema['type'] == 'object'
		assert 'properties' in schema
		assert 'clusters' in schema['properties']
		assert schema['required'] == ['clusters']
		assert schema['additionalProperties'] is False

		# verify clusters array structure
		clusters_schema = schema['properties']['clusters']
		assert clusters_schema['type'] == 'array'
		assert 'items' in clusters_schema

		# verify cluster item properties
		cluster_item = clusters_schema['items']
		assert cluster_item['type'] == 'object'
		assert 'properties' in cluster_item

		# verify required fields
		required_fields = cluster_item['required']
		assert 'topic_name' in required_fields
		assert 'product' in required_fields
		assert 'category' in required_fields
		assert 'subcategory' in required_fields
		assert 'ticket_indices' in required_fields
		assert 'summary' in required_fields

	def test_get_output_schema_field_types(self):
		"""Test output schema has correct field types."""
		schema = get_output_schema()
		cluster_properties = schema['properties']['clusters']['items']['properties']

		# verify string fields
		assert cluster_properties['topic_name']['type'] == 'string'
		assert cluster_properties['product']['type'] == 'string'
		assert cluster_properties['category']['type'] == 'string'
		assert cluster_properties['subcategory']['type'] == 'string'
		assert cluster_properties['summary']['type'] == 'string'

		# verify ticket_indices is array of integers
		assert cluster_properties['ticket_indices']['type'] == 'array'
		assert cluster_properties['ticket_indices']['items']['type'] == 'integer'
