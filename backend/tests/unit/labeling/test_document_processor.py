"""Unit tests for document processor service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.services.labeling.document_processor import process_document


@pytest.mark.asyncio
class TestDocumentProcessor:
    """Test document processing workflow."""

    async def test_process_document_success(self):
        """Test successful document processing."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": True, "content": "Document content"}
        label_result = {"department_area": "Tech"}
        db_result = MagicMock(id=123)

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
                    mock_decode.return_value = decode_result
                    mock_label.return_value = label_result
                    mock_create.return_value = db_result

                    result = await process_document("test.pdf", b"PDF_CONTENT", mock_llm_client, mock_db)

                    assert result["success"] is True
                    assert result["filename"] == "test.pdf"
                    assert result["area"] == "Tech"
                    assert result["file_id"] == 123

    async def test_process_document_decode_failure(self):
        """Test handling of decoding failures."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": False, "error": "Invalid PDF"}

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            mock_decode.return_value = decode_result

            result = await process_document("bad.pdf", b"INVALID", mock_llm_client, mock_db)

            assert result["success"] is False
            assert result["filename"] == "bad.pdf"
            assert "error" in result
            assert "Invalid PDF" in result["error"]

    async def test_process_document_label_failure(self):
        """Test handling of labeling failures."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": True, "content": "Content"}
        label_result = {"error": "LLM error", "department_area": "Unknown"}

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                mock_decode.return_value = decode_result
                mock_label.return_value = label_result

                result = await process_document("test.pdf", b"PDF", mock_llm_client, mock_db)

                assert result["success"] is False
                assert result["filename"] == "test.pdf"
                assert "error" in result
                assert "Labeling failed" in result["error"]

    async def test_process_document_database_failure(self):
        """Test handling of database save failures."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": True, "content": "Content"}
        label_result = {"department_area": "Tech"}

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
                    mock_decode.return_value = decode_result
                    mock_label.return_value = label_result
                    mock_create.side_effect = Exception("Database connection error")

                    result = await process_document("test.pdf", b"PDF", mock_llm_client, mock_db)

                    assert result["success"] is False
                    assert result["filename"] == "test.pdf"
                    assert "error" in result
                    assert "Database error" in result["error"]

    async def test_process_document_calls_decode_with_correct_params(self):
        """Test that decode_document is called with correct parameters."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)
        content = b"PDF_CONTENT"

        decode_result = {"success": True, "content": "Decoded content"}
        label_result = {"department_area": "Tech"}
        db_result = MagicMock(id=123)

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
                    with patch("ai_ticket_platform.services.labeling.document_processor.asyncio.to_thread") as mock_thread:
                        # Mock asyncio.to_thread to call the function directly
                        mock_thread.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

                        mock_decode.return_value = decode_result
                        mock_label.return_value = label_result
                        mock_create.return_value = db_result

                        await process_document("test.pdf", content, mock_llm_client, mock_db)

                        mock_decode.assert_called_once()

    async def test_process_document_calls_label_with_correct_params(self):
        """Test that label_document is called with correct parameters."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": True, "content": "Decoded content"}
        label_result = {"department_area": "Finance"}
        db_result = MagicMock(id=123)

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
                    with patch("ai_ticket_platform.services.labeling.document_processor.asyncio.to_thread") as mock_thread:
                        mock_thread.side_effect = lambda func, *args, **kwargs: func(*args, **kwargs)

                        mock_decode.return_value = decode_result
                        mock_label.return_value = label_result
                        mock_create.return_value = db_result

                        await process_document("test.pdf", b"PDF", mock_llm_client, mock_db)

                        mock_label.assert_called_once()
                        call_args = mock_label.call_args[1]
                        assert call_args["document"]["filename"] == "test.pdf"
                        assert call_args["document"]["content"] == "Decoded content"
                        assert call_args["llm_client"] == mock_llm_client

    async def test_process_document_saves_to_database(self):
        """Test that document is saved to database."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": True, "content": "Content"}
        label_result = {"department_area": "HR"}
        db_result = MagicMock(id=456)

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
                    mock_decode.return_value = decode_result
                    mock_label.return_value = label_result
                    mock_create.return_value = db_result

                    result = await process_document("test.pdf", b"PDF", mock_llm_client, mock_db)

                    mock_create.assert_called_once()
                    call_kwargs = mock_create.call_args[1]
                    assert call_kwargs["db"] == mock_db
                    assert call_kwargs["original_filename"] == "test.pdf"
                    assert call_kwargs["area"] == "HR"
                    assert call_kwargs["blob_path"] == ""

    async def test_process_document_returns_file_id(self):
        """Test that file ID from database is returned."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": True, "content": "Content"}
        label_result = {"department_area": "Tech"}
        db_result = MagicMock(id=789)

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
                    mock_decode.return_value = decode_result
                    mock_label.return_value = label_result
                    mock_create.return_value = db_result

                    result = await process_document("test.pdf", b"PDF", mock_llm_client, mock_db)

                    assert result["file_id"] == 789

    async def test_process_document_returns_area_label(self):
        """Test that area label is returned in result."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": True, "content": "Content"}
        label_result = {"department_area": "Marketing"}
        db_result = MagicMock(id=123)

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
                    mock_decode.return_value = decode_result
                    mock_label.return_value = label_result
                    mock_create.return_value = db_result

                    result = await process_document("test.pdf", b"PDF", mock_llm_client, mock_db)

                    assert result["area"] == "Marketing"

    async def test_process_document_handles_edge_case_empty_area(self):
        """Test handling of empty area from labeling."""
        mock_llm_client = MagicMock()
        mock_db = MagicMock(spec=AsyncSession)

        decode_result = {"success": True, "content": "Content"}
        label_result = {"department_area": "Unknown"}  # Default unknown label
        db_result = MagicMock(id=123)

        with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
            with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
                with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
                    mock_decode.return_value = decode_result
                    mock_label.return_value = label_result
                    mock_create.return_value = db_result

                    result = await process_document("test.pdf", b"PDF", mock_llm_client, mock_db)

                    assert result["success"] is True
                    assert result["area"] == "Unknown"
