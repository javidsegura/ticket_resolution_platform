"""Unit tests for documents router endpoint."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.routers.documents import router


@pytest.mark.asyncio
class TestUploadCompanyDocuments:
	"""Test document upload endpoint."""

	async def test_upload_single_pdf_success(self):
		"""Test successful upload of a single PDF document."""
		# Mock file
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "budget.pdf"
		mock_file.read = AsyncMock(return_value=b"PDF_CONTENT")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_result = {
			"filename": "budget.pdf",
			"success": True,
			"area": "Finance",
			"file_id": 123
		}

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.return_value = process_result

				result = await router.routes[0].endpoint(
					files=[mock_file],
					settings=mock_settings,
					db=mock_db
				)

				assert result["total_processed"] == 1
				assert result["successful"] == 1
				assert result["failed"] == 0
				assert result["results"][0]["success"] is True
				assert result["results"][0]["filename"] == "budget.pdf"

	async def test_upload_multiple_pdf_success(self):
		"""Test successful upload of multiple PDF documents."""
		# Mock files
		mock_file1 = MagicMock(spec=UploadFile)
		mock_file1.filename = "budget.pdf"
		mock_file1.read = AsyncMock(return_value=b"PDF_CONTENT_1")

		mock_file2 = MagicMock(spec=UploadFile)
		mock_file2.filename = "report.pdf"
		mock_file2.read = AsyncMock(return_value=b"PDF_CONTENT_2")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_results = [
			{"filename": "budget.pdf", "success": True, "area": "Finance", "file_id": 123},
			{"filename": "report.pdf", "success": True, "area": "Tech", "file_id": 124}
		]

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.side_effect = process_results

				result = await router.routes[0].endpoint(
					files=[mock_file1, mock_file2],
					settings=mock_settings,
					db=mock_db
				)

				assert result["total_processed"] == 2
				assert result["successful"] == 2
				assert result["failed"] == 0
				assert len(result["results"]) == 2

	async def test_upload_non_pdf_file_rejected(self):
		"""Test that non-PDF files are rejected."""
		# Mock non-PDF file
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "document.txt"
		mock_file.read = AsyncMock(return_value=b"TEXT_CONTENT")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client"):
			result = await router.routes[0].endpoint(
				files=[mock_file],
				settings=mock_settings,
				db=mock_db
			)

			assert result["total_processed"] == 1
			assert result["successful"] == 0
			assert result["failed"] == 1
			assert result["results"][0]["success"] is False
			assert "Only PDF files are accepted" in result["results"][0]["error"]

	async def test_upload_mixed_pdf_and_non_pdf(self):
		"""Test upload with mix of PDF and non-PDF files."""
		# Mock files
		mock_pdf = MagicMock(spec=UploadFile)
		mock_pdf.filename = "budget.pdf"
		mock_pdf.read = AsyncMock(return_value=b"PDF_CONTENT")

		mock_txt = MagicMock(spec=UploadFile)
		mock_txt.filename = "notes.txt"
		mock_txt.read = AsyncMock(return_value=b"TEXT")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_result = {
			"filename": "budget.pdf",
			"success": True,
			"area": "Finance",
			"file_id": 123
		}

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.return_value = process_result

				result = await router.routes[0].endpoint(
					files=[mock_pdf, mock_txt],
					settings=mock_settings,
					db=mock_db
				)

				assert result["total_processed"] == 2
				assert result["successful"] == 1
				assert result["failed"] == 1
				assert result["results"][0]["success"] is True
				assert result["results"][1]["success"] is False

	async def test_upload_pdf_processing_failure(self):
		"""Test handling of PDF processing failures."""
		# Mock file
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "corrupted.pdf"
		mock_file.read = AsyncMock(return_value=b"INVALID_PDF")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_result = {
			"filename": "corrupted.pdf",
			"success": False,
			"error": "Failed to process PDF"
		}

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.return_value = process_result

				result = await router.routes[0].endpoint(
					files=[mock_file],
					settings=mock_settings,
					db=mock_db
				)

				assert result["total_processed"] == 1
				assert result["successful"] == 0
				assert result["failed"] == 1
				assert result["results"][0]["success"] is False

	async def test_upload_calls_process_document_with_correct_params(self):
		"""Test that process_document is called with correct parameters."""
		# Mock file
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "test.pdf"
		content = b"PDF_CONTENT"
		mock_file.read = AsyncMock(return_value=content)

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_result = {
			"filename": "test.pdf",
			"success": True,
			"area": "Tech",
			"file_id": 123
		}

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.return_value = process_result

				await router.routes[0].endpoint(
					files=[mock_file],
					settings=mock_settings,
					db=mock_db
				)

				# Verify process_document called with correct params
				mock_process.assert_called_once()
				call_kwargs = mock_process.call_args[1]
				assert call_kwargs["filename"] == "test.pdf"
				assert call_kwargs["content"] == content
				assert call_kwargs["llm_client"] == mock_llm_client
				assert call_kwargs["db"] == mock_db

	async def test_upload_initializes_llm_client_with_settings(self):
		"""Test that LLM client is initialized with settings."""
		# Mock file
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "test.pdf"
		mock_file.read = AsyncMock(return_value=b"PDF")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_result = {
			"filename": "test.pdf",
			"success": True,
			"area": "Tech",
			"file_id": 123
		}

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.return_value = process_result

				await router.routes[0].endpoint(
					files=[mock_file],
					settings=mock_settings,
					db=mock_db
				)

				# Verify LLM client initialized with settings
				mock_init_llm.assert_called_once_with(mock_settings)

	async def test_upload_processes_files_sequentially(self):
		"""Test that files are processed sequentially (not concurrently)."""
		# Mock files
		mock_file1 = MagicMock(spec=UploadFile)
		mock_file1.filename = "first.pdf"
		mock_file1.read = AsyncMock(return_value=b"PDF_1")

		mock_file2 = MagicMock(spec=UploadFile)
		mock_file2.filename = "second.pdf"
		mock_file2.read = AsyncMock(return_value=b"PDF_2")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_results = [
			{"filename": "first.pdf", "success": True, "area": "Finance", "file_id": 1},
			{"filename": "second.pdf", "success": True, "area": "Tech", "file_id": 2}
		]

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.side_effect = process_results

				result = await router.routes[0].endpoint(
					files=[mock_file1, mock_file2],
					settings=mock_settings,
					db=mock_db
				)

				# Verify both files were processed
				assert mock_process.call_count == 2

				# Verify first file processed first
				first_call = mock_process.call_args_list[0]
				assert first_call[1]["filename"] == "first.pdf"

				# Verify second file processed second
				second_call = mock_process.call_args_list[1]
				assert second_call[1]["filename"] == "second.pdf"

	async def test_upload_empty_file_list(self):
		"""Test upload with empty file list."""
		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client"):
			result = await router.routes[0].endpoint(
				files=[],
				settings=mock_settings,
				db=mock_db
			)

			assert result["total_processed"] == 0
			assert result["successful"] == 0
			assert result["failed"] == 0
			assert result["results"] == []

	async def test_upload_case_insensitive_pdf_check(self):
		"""Test that PDF file extension check is case-insensitive."""
		# Test uppercase extension
		mock_file_upper = MagicMock(spec=UploadFile)
		mock_file_upper.filename = "document.PDF"
		mock_file_upper.read = AsyncMock(return_value=b"PDF_CONTENT")

		# Test mixed case extension
		mock_file_mixed = MagicMock(spec=UploadFile)
		mock_file_mixed.filename = "report.Pdf"
		mock_file_mixed.read = AsyncMock(return_value=b"PDF_CONTENT")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_results = [
			{"filename": "document.PDF", "success": True, "area": "Finance", "file_id": 1},
			{"filename": "report.Pdf", "success": True, "area": "Tech", "file_id": 2}
		]

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.side_effect = process_results

				result = await router.routes[0].endpoint(
					files=[mock_file_upper, mock_file_mixed],
					settings=mock_settings,
					db=mock_db
				)

				assert result["successful"] == 2
				assert result["failed"] == 0

	async def test_upload_response_structure(self):
		"""Test that response has correct structure."""
		# Mock file
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "test.pdf"
		mock_file.read = AsyncMock(return_value=b"PDF")

		# Mock dependencies
		mock_settings = MagicMock()
		mock_db = MagicMock(spec=AsyncSession)
		mock_llm_client = MagicMock()

		process_result = {
			"filename": "test.pdf",
			"success": True,
			"area": "Tech",
			"file_id": 123
		}

		with patch("ai_ticket_platform.routers.documents.initialize_llm_client") as mock_init_llm:
			with patch("ai_ticket_platform.routers.documents.process_document", new_callable=AsyncMock) as mock_process:
				mock_init_llm.return_value = mock_llm_client
				mock_process.return_value = process_result

				result = await router.routes[0].endpoint(
					files=[mock_file],
					settings=mock_settings,
					db=mock_db
				)

				# Verify response structure
				assert "total_processed" in result
				assert "successful" in result
				assert "failed" in result
				assert "results" in result
				assert isinstance(result["results"], list)
