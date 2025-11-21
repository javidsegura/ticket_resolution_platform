import pytest
from unittest.mock import Mock, AsyncMock, patch

from ai_ticket_platform.services.labeling.document_processor import process_document
from ai_ticket_platform.core.clients import LLMClient


class TestProcessDocument:
	"""Test suite for process_document function."""

	@pytest.fixture
	def mock_llm_client(self):
		"""Create mock LLM client."""
		client = Mock(spec=LLMClient)
		return client

	@pytest.fixture
	def mock_db(self):
		"""Create mock database session."""
		db = AsyncMock()
		return db

	@pytest.mark.asyncio
	async def test_process_document_success(self, mock_llm_client, mock_db):
		"""Test successful document processing workflow."""
		# setup
		filename = "test_doc.pdf"
		content = b"PDF document content"

		# mock decode_document
		with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
			mock_decode.return_value = {
				"success": True,
				"content": "PDF document content"
			}

			# mock label_document
			with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
				mock_label.return_value = {
					"department_area": "Tech"
				}

				# mock create_company_file
				with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
					mock_db_file = Mock()
					mock_db_file.id = 123
					mock_create.return_value = mock_db_file

					# execute
					result = await process_document(
						filename=filename,
						content=content,
						llm_client=mock_llm_client,
						db=mock_db
					)

					# verify
					assert result["success"] is True
					assert result["filename"] == filename
					assert result["area"] == "Tech"
					assert result["file_id"] == 123

					# verify all steps were called
					mock_decode.assert_called_once_with(filename, content)
					mock_label.assert_called_once()
					mock_create.assert_called_once()

	@pytest.mark.asyncio
	async def test_process_document_decode_failure(self, mock_llm_client, mock_db):
		"""Test handling of decode failure."""
		# setup
		filename = "bad_encoding.pdf"
		content = b"Invalid content"

		# mock decode_document to fail
		with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
			mock_decode.return_value = {
				"success": False,
				"error": "File encoding not supported"
			}

			# execute
			result = await process_document(
				filename=filename,
				content=content,
				llm_client=mock_llm_client,
				db=mock_db
			)

			# verify
			assert result["success"] is False
			assert result["filename"] == filename
			assert "error" in result
			assert "encoding" in result["error"].lower()

	@pytest.mark.asyncio
	async def test_process_document_label_failure(self, mock_llm_client, mock_db):
		"""Test handling of labeling failure."""
		# setup
		filename = "label_fail.pdf"
		content = b"PDF content"

		# mock decode_document success
		with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
			mock_decode.return_value = {
				"success": True,
				"content": "PDF content"
			}

			# mock label_document to return error
			with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
				mock_label.return_value = {
					"error": "LLM API rate limit exceeded"
				}

				# execute
				result = await process_document(
					filename=filename,
					content=content,
					llm_client=mock_llm_client,
					db=mock_db
				)

				# verify
				assert result["success"] is False
				assert result["filename"] == filename
				assert "Labeling failed" in result["error"]

	@pytest.mark.asyncio
	async def test_process_document_database_failure(self, mock_llm_client, mock_db):
		"""Test handling of database save failure."""
		# setup
		filename = "db_fail.pdf"
		content = b"PDF content"

		# mock decode_document
		with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
			mock_decode.return_value = {
				"success": True,
				"content": "PDF content"
			}

			# mock label_document
			with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
				mock_label.return_value = {
					"department_area": "Finance"
				}

				# mock create_company_file to raise exception
				with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
					mock_create.side_effect = Exception("Database connection error")

					# execute
					result = await process_document(
						filename=filename,
						content=content,
						llm_client=mock_llm_client,
						db=mock_db
					)

					# verify
					assert result["success"] is False
					assert result["filename"] == filename
					assert "Database error" in result["error"]

	@pytest.mark.asyncio
	async def test_process_document_unknown_area_default(self, mock_llm_client, mock_db):
		"""Test that missing department_area defaults to 'Unknown'."""
		# setup
		filename = "no_area.pdf"
		content = b"PDF content"

		# mock decode_document
		with patch("ai_ticket_platform.services.labeling.document_processor.decode_document") as mock_decode:
			mock_decode.return_value = {
				"success": True,
				"content": "PDF content"
			}

			# mock label_document without department_area
			with patch("ai_ticket_platform.services.labeling.document_processor.label_document") as mock_label:
				mock_label.return_value = {}

				# mock create_company_file
				with patch("ai_ticket_platform.services.labeling.document_processor.create_company_file") as mock_create:
					mock_db_file = Mock()
					mock_db_file.id = 456
					mock_create.return_value = mock_db_file

					# execute
					result = await process_document(
						filename=filename,
						content=content,
						llm_client=mock_llm_client,
						db=mock_db
					)

					# verify
					assert result["success"] is True
					assert result["area"] == "Unknown"
					mock_create.assert_called_once()
					# verify area parameter was "Unknown"
					call_kwargs = mock_create.call_args[1]
					assert call_kwargs["area"] == "Unknown"
