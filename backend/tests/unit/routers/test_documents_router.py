"""Unit tests for documents router endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestUploadCompanyDocuments:
	"""Test POST /documents/upload endpoint."""

	async def test_upload_documents_success(self):
		"""Test successfully uploading PDF documents."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()

		async def mock_get_db():
			yield mock_db

		async def mock_get_settings():
			return mock_settings

		mock_process_result = {
			"filename": "test.pdf",
			"success": True,
			"indexed": True,
		}

		with patch("ai_ticket_platform.routers.documents.get_db", mock_get_db):
			with patch("ai_ticket_platform.routers.documents.get_app_settings", mock_get_settings):
				with patch("ai_ticket_platform.routers.documents.get_llm_client", return_value=MagicMock()):
					with patch("ai_ticket_platform.routers.documents.process_and_index_document", new=AsyncMock(return_value=mock_process_result)):
						async with AsyncClient(
							transport=ASGITransport(app=app),
							base_url="http://test"
						) as client:
							files = [
								("files", ("test.pdf", b"PDF content", "application/pdf"))
							]
							response = await client.post("/api/documents/upload", files=files)

							assert response.status_code == 200
							data = response.json()
							assert data["total_processed"] == 1
							assert data["successful"] == 1
							assert data["failed"] == 0
							assert data["indexed"] == 1
							assert len(data["results"]) == 1
							assert data["results"][0]["success"] is True

	async def test_upload_documents_non_pdf_rejected(self):
		"""Test that non-PDF files are rejected."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()

		async def mock_get_db():
			yield mock_db

		async def mock_get_settings():
			return mock_settings

		with patch("ai_ticket_platform.routers.documents.get_db", mock_get_db):
			with patch("ai_ticket_platform.routers.documents.get_app_settings", mock_get_settings):
				with patch("ai_ticket_platform.routers.documents.get_llm_client", return_value=MagicMock()):
					async with AsyncClient(
						transport=ASGITransport(app=app),
						base_url="http://test"
					) as client:
						files = [
							("files", ("test.txt", b"Text content", "text/plain"))
						]
						response = await client.post("/api/documents/upload", files=files)

						assert response.status_code == 200
						data = response.json()
						assert data["total_processed"] == 1
						assert data["successful"] == 0
						assert data["failed"] == 1
						assert data["indexed"] == 0
						assert data["results"][0]["success"] is False
						assert "Only PDF files are accepted" in data["results"][0]["error"]

	async def test_upload_documents_multiple_files(self):
		"""Test uploading multiple PDF documents."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()

		async def mock_get_db():
			yield mock_db

		async def mock_get_settings():
			return mock_settings

		mock_success_result = {"filename": "test1.pdf", "success": True, "indexed": True}
		mock_fail_result = {"filename": "test2.pdf", "success": False, "indexed": False}

		with patch("ai_ticket_platform.routers.documents.get_db", mock_get_db):
			with patch("ai_ticket_platform.routers.documents.get_app_settings", mock_get_settings):
				with patch("ai_ticket_platform.routers.documents.get_llm_client", return_value=MagicMock()):
					with patch("ai_ticket_platform.routers.documents.process_and_index_document", new=AsyncMock(side_effect=[mock_success_result, mock_fail_result])):
						async with AsyncClient(
							transport=ASGITransport(app=app),
							base_url="http://test"
						) as client:
							files = [
								("files", ("test1.pdf", b"PDF content 1", "application/pdf")),
								("files", ("test2.pdf", b"PDF content 2", "application/pdf"))
							]
							response = await client.post("/api/documents/upload", files=files)

							assert response.status_code == 200
							data = response.json()
							assert data["total_processed"] == 2
							assert data["successful"] == 1
							assert data["failed"] == 1
							assert data["indexed"] == 1
							assert len(data["results"]) == 2

	async def test_upload_documents_mixed_file_types(self):
		"""Test uploading mix of PDF and non-PDF files."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()

		async def mock_get_db():
			yield mock_db

		async def mock_get_settings():
			return mock_settings

		mock_success_result = {"filename": "test.pdf", "success": True, "indexed": True}

		with patch("ai_ticket_platform.routers.documents.get_db", mock_get_db):
			with patch("ai_ticket_platform.routers.documents.get_app_settings", mock_get_settings):
				with patch("ai_ticket_platform.routers.documents.get_llm_client", return_value=MagicMock()):
					with patch("ai_ticket_platform.routers.documents.process_and_index_document", new=AsyncMock(return_value=mock_success_result)):
						async with AsyncClient(
							transport=ASGITransport(app=app),
							base_url="http://test"
						) as client:
							files = [
								("files", ("test.pdf", b"PDF content", "application/pdf")),
								("files", ("test.docx", b"Word content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
							]
							response = await client.post("/api/documents/upload", files=files)

							assert response.status_code == 200
							data = response.json()
							assert data["total_processed"] == 2
							assert data["successful"] == 1
							assert data["failed"] == 1
							# Only the PDF should be indexed
							assert data["indexed"] == 1
