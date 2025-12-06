"""Unit tests for label service."""

import pytest
from unittest.mock import MagicMock, patch
from ai_ticket_platform.services.company_docs.label_service import label_document


class TestLabelDocument:
    """Test document labeling service."""

    def test_label_document_success(self):
        """Test successful document labeling."""
        document = {"filename": "test.pdf", "content": "This is a technical document about APIs"}
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "department_area": "Tech"
        }

        with patch("ai_ticket_platform.services.company_docs.label_service.prompt_builder") as mock_pb:
            mock_pb.build_labeling_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}
            mock_pb.get_task_config.return_value = {}

            result = label_document(document, mock_llm_client)

            # Service doesn't return 'success' field on success
            assert "filename" in result
            assert result["filename"] == "test.pdf"
            assert "department_area" in result
            assert result["department_area"] == "Tech"

    def test_label_document_with_empty_content(self):
        """Test labeling document with empty content."""
        document = {"filename": "empty.pdf", "content": ""}
        mock_llm_client = MagicMock()

        result = label_document(document, mock_llm_client)

        assert "error" in result
        assert result["filename"] == "empty.pdf"
        assert result["department_area"] == "Unknown"

    def test_label_document_with_whitespace_only_content(self):
        """Test labeling document with whitespace-only content."""
        document = {"filename": "whitespace.pdf", "content": "   \n\t  "}
        mock_llm_client = MagicMock()

        result = label_document(document, mock_llm_client)

        assert "error" in result
        assert result["filename"] == "whitespace.pdf"
        assert result["department_area"] == "Unknown"

    def test_label_document_calls_llm_with_correct_params(self):
        """Test that LLM is called with correct parameters."""
        document = {"filename": "test.pdf", "content": "Technical document"}
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "department_area": "Tech"
        }

        with patch("ai_ticket_platform.services.company_docs.label_service.prompt_builder") as mock_pb:
            mock_pb.build_labeling_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}
            mock_pb.get_task_config.return_value = {}

            label_document(document, mock_llm_client)

            mock_pb.build_labeling_prompt.assert_called_once()
            call_kwargs = mock_pb.build_labeling_prompt.call_args[1]
            assert call_kwargs["filename"] == "test.pdf"
            assert call_kwargs["document_content"] == "Technical document"

    def test_label_document_detects_invalid_llm_response(self):
        """Test handling of invalid LLM response."""
        document = {"filename": "test.pdf", "content": "Valid content"}
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {"invalid": "response"}

        with patch("ai_ticket_platform.services.company_docs.label_service.prompt_builder") as mock_pb:
            mock_pb.build_labeling_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}
            mock_pb.get_task_config.return_value = {}

            result = label_document(document, mock_llm_client)

            assert "error" in result
            assert result["department_area"] == "Unknown"
            assert result["filename"] == "test.pdf"

    def test_label_document_handles_llm_exception(self):
        """Test handling of LLM exceptions."""
        document = {"filename": "test.pdf", "content": "Valid content"}
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.side_effect = Exception("LLM API error")

        with patch("ai_ticket_platform.services.company_docs.label_service.prompt_builder") as mock_pb:
            mock_pb.build_labeling_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}
            mock_pb.get_task_config.return_value = {}

            result = label_document(document, mock_llm_client)

            assert "error" in result
            assert result["department_area"] == "Unknown"
            assert "LLM API error" in result["error"]

    def test_label_document_missing_filename(self):
        """Test labeling document with missing filename."""
        document = {"content": "Some content"}
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "department_area": "Tech"
        }

        with patch("ai_ticket_platform.services.company_docs.label_service.prompt_builder") as mock_pb:
            mock_pb.build_labeling_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}
            mock_pb.get_task_config.return_value = {}

            result = label_document(document, mock_llm_client)

            assert result["filename"] == "unknown"
            assert "department_area" in result

    def test_label_document_temperature_setting(self):
        """Test that temperature is set to 0.3 for deterministic labeling."""
        document = {"filename": "test.pdf", "content": "Content"}
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "department_area": "Tech"
        }

        with patch("ai_ticket_platform.services.company_docs.label_service.prompt_builder") as mock_pb:
            mock_pb.build_labeling_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}
            mock_pb.get_task_config.return_value = {}

            label_document(document, mock_llm_client)

            call_kwargs = mock_llm_client.call_llm_structured.call_args[1]
            assert call_kwargs["temperature"] == 0.3

    def test_label_document_returns_department_area(self):
        """Test that department_area is returned in result."""
        document = {"filename": "test.pdf", "content": "Content"}
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "department_area": "Finance"
        }

        with patch("ai_ticket_platform.services.company_docs.label_service.prompt_builder") as mock_pb:
            mock_pb.build_labeling_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}
            mock_pb.get_task_config.return_value = {}

            result = label_document(document, mock_llm_client)

            assert result["department_area"] == "Finance"

    def test_label_document_preserves_llm_response_fields(self):
        """Test that additional fields from LLM response are preserved."""
        document = {"filename": "test.pdf", "content": "Content"}
        mock_llm_client = MagicMock()
        mock_llm_client.call_llm_structured.return_value = {
            "department_area": "HR",
            "confidence": 0.95,
            "related_areas": ["Finance", "Legal"]
        }

        with patch("ai_ticket_platform.services.company_docs.label_service.prompt_builder") as mock_pb:
            mock_pb.build_labeling_prompt.return_value = "Test prompt"
            mock_pb.get_output_schema.return_value = {}
            mock_pb.get_task_config.return_value = {}

            result = label_document(document, mock_llm_client)

            assert result["department_area"] == "HR"
            assert result["confidence"] == 0.95
            assert result["related_areas"] == ["Finance", "Legal"]
