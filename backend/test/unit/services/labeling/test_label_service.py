import pytest
from unittest.mock import Mock, patch

from ai_ticket_platform.services.labeling.label_service import label_document
from ai_ticket_platform.core.clients import LLMClient


class TestLabelDocument:
	"""Test suite for label_document function."""

	@pytest.fixture
	def mock_llm_client(self):
		"""Create mock LLM client."""
		client = Mock(spec=LLMClient)
		return client

	def test_label_document_success(self, mock_llm_client):
		"""Test successful document labeling."""
		# setup
		document = {
			"filename": "test.pdf",
			"content": "This is a technical document about API integration and software architecture."
		}

		# mock LLM response
		mock_llm_client.call_llm_structured.return_value = {
			"department_area": "Tech"
		}

		# mock the prompt builder functions
		with patch("ai_ticket_platform.services.labeling.label_service.prompt_builder") as mock_builder:
			mock_builder.build_labeling_prompt.return_value = "mocked prompt"
			mock_builder.get_output_schema.return_value = {"type": "object"}
			mock_builder.get_task_config.return_value = {"system_prompt": "test"}

			# execute
			result = label_document(document=document, llm_client=mock_llm_client)

			# verify
			assert result["filename"] == "test.pdf"
			assert result["department_area"] == "Tech"
			assert "error" not in result

			# verify LLM was called correctly
			mock_llm_client.call_llm_structured.assert_called_once()
			call_kwargs = mock_llm_client.call_llm_structured.call_args[1]
			assert call_kwargs["prompt"] == "mocked prompt"
			assert call_kwargs["temperature"] == 0.3

	def test_label_document_empty_content(self, mock_llm_client):
		"""Test labeling document with empty content."""
		# setup
		document = {
			"filename": "empty.pdf",
			"content": ""
		}

		# execute
		result = label_document(document=document, llm_client=mock_llm_client)

		# verify
		assert result["filename"] == "empty.pdf"
		assert result["department_area"] == "Unknown"
		assert "error" in result
		assert "empty" in result["error"].lower()

		# verify LLM was NOT called
		mock_llm_client.call_llm_structured.assert_not_called()

	def test_label_document_llm_exception(self, mock_llm_client):
		"""Test handling of LLM client exceptions."""
		# setup
		document = {
			"filename": "test.pdf",
			"content": "Test content"
		}

		# mock LLM to raise exception
		mock_llm_client.call_llm_structured.side_effect = Exception("API error: rate limit exceeded")

		with patch("ai_ticket_platform.services.labeling.label_service.prompt_builder") as mock_builder:
			mock_builder.build_labeling_prompt.return_value = "prompt"
			mock_builder.get_output_schema.return_value = {"type": "object"}
			mock_builder.get_task_config.return_value = {"system_prompt": "test"}

			# execute
			result = label_document(document=document, llm_client=mock_llm_client)

			# verify
			assert result["filename"] == "test.pdf"
			assert result["department_area"] == "Unknown"
			assert "error" in result
			assert "API error" in result["error"]

	def test_label_document_preserves_llm_response_fields(self, mock_llm_client):
		"""Test that additional fields from LLM response are preserved."""
		# setup
		document = {
			"filename": "test.pdf",
			"content": "Test content"
		}

		# mock LLM response with additional fields
		mock_llm_client.call_llm_structured.return_value = {
			"department_area": "Marketing",
			"confidence": 0.95,
			"reasoning": "Contains marketing strategy keywords"
		}

		with patch("ai_ticket_platform.services.labeling.label_service.prompt_builder") as mock_builder:
			mock_builder.build_labeling_prompt.return_value = "prompt"
			mock_builder.get_output_schema.return_value = {"type": "object"}
			mock_builder.get_task_config.return_value = {"system_prompt": "test"}

			# execute
			result = label_document(document=document, llm_client=mock_llm_client)

			# verify
			assert result["filename"] == "test.pdf"
			assert result["department_area"] == "Marketing"
			# Additional fields should be preserved
			assert result.get("confidence") == 0.95
			assert result.get("reasoning") == "Contains marketing strategy keywords"
