import asyncio
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.ai_ticket_platform.dependencies.settings import get_app_settings
from src.ai_ticket_platform.dependencies.database import get_db
from src.ai_ticket_platform.routers import documents as documents_router


@pytest.fixture()
def test_app():
	"""Create test FastAPI application with documents router."""
	app = FastAPI()
	app.include_router(documents_router.router, prefix="/api")

	mock_settings = SimpleNamespace(
		GEMINI_API_KEY="test-api-key",
		GEMINI_MODEL="gemini-2.5-flash",
	)

	async def override_settings():
		return mock_settings

	async def override_db():
		"""Mock database session."""
		mock_db = Mock()
		yield mock_db

	app.dependency_overrides[get_app_settings] = override_settings
	app.dependency_overrides[get_db] = override_db
	return app


async def _post_multipart(app: FastAPI, path: str, files: list):
	"""Helper to post multipart form data with files."""
	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as client:
		files_data = [("files", (file["name"], file["content"], file["type"])) for file in files]
		return await client.post(path, files=files_data)


def test_upload_single_pdf_success(monkeypatch, test_app: FastAPI):
	"""Test successful upload of a single PDF document."""

	# mock the process_document function
	mock_process_result = {
		"filename": "test.pdf",
		"success": True,
		"area": "Tech",
		"file_id": 1
	}

	with patch("ai_ticket_platform.routers.documents.process_document", return_value=mock_process_result):
		with patch("ai_ticket_platform.routers.documents.initialize_llm_client"):
			async def _run():
				files = [{
					"name": "test.pdf",
					"content": BytesIO(b"PDF content here"),
					"type": "application/pdf"
				}]

				response = await _post_multipart(test_app, "/api/documents/upload", files)

				assert response.status_code == 200
				json_response = response.json()
				assert json_response["total_processed"] == 1
				assert json_response["successful"] == 1
				assert json_response["failed"] == 0
				assert len(json_response["results"]) == 1
				assert json_response["results"][0]["filename"] == "test.pdf"
				assert json_response["results"][0]["success"] is True
				assert json_response["results"][0]["area"] == "Tech"

			asyncio.run(_run())


def test_upload_multiple_pdfs_success(monkeypatch, test_app: FastAPI):
	"""Test successful upload of multiple PDF documents."""

	# mock the process_document function to return different results
	def mock_process_side_effect(**kwargs):
		filename = kwargs.get("filename")
		if filename == "doc1.pdf":
			return {"filename": filename, "success": True, "area": "Finance", "file_id": 1}
		elif filename == "doc2.pdf":
			return {"filename": filename, "success": True, "area": "HR", "file_id": 2}
		else:
			return {"filename": filename, "success": True, "area": "Tech", "file_id": 3}

	with patch("ai_ticket_platform.routers.documents.process_document", side_effect=mock_process_side_effect):
		with patch("ai_ticket_platform.routers.documents.initialize_llm_client"):
			async def _run():
				files = [
					{"name": "doc1.pdf", "content": BytesIO(b"PDF 1"), "type": "application/pdf"},
					{"name": "doc2.pdf", "content": BytesIO(b"PDF 2"), "type": "application/pdf"},
					{"name": "doc3.pdf", "content": BytesIO(b"PDF 3"), "type": "application/pdf"},
				]

				response = await _post_multipart(test_app, "/api/documents/upload", files)

				assert response.status_code == 200
				json_response = response.json()
				assert json_response["total_processed"] == 3
				assert json_response["successful"] == 3
				assert json_response["failed"] == 0
				assert len(json_response["results"]) == 3

			asyncio.run(_run())


def test_upload_non_pdf_file_rejected(monkeypatch, test_app: FastAPI):
	"""Test that non-PDF files are rejected."""

	with patch("ai_ticket_platform.routers.documents.initialize_llm_client"):
		async def _run():
			files = [{
				"name": "document.docx",
				"content": BytesIO(b"Word document content"),
				"type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
			}]

			response = await _post_multipart(test_app, "/api/documents/upload", files)

			assert response.status_code == 200
			json_response = response.json()
			assert json_response["total_processed"] == 1
			assert json_response["successful"] == 0
			assert json_response["failed"] == 1
			assert json_response["results"][0]["success"] is False
			assert "Only PDF files are accepted" in json_response["results"][0]["error"]

		asyncio.run(_run())


def test_upload_mixed_files_partial_success(monkeypatch, test_app: FastAPI):
	"""Test upload with mix of valid PDFs and invalid files."""

	def mock_process_side_effect(**kwargs):
		filename = kwargs.get("filename")
		if filename == "valid.pdf":
			return {"filename": filename, "success": True, "area": "Tech", "file_id": 1}
		else:
			return {"filename": filename, "success": False, "error": "Processing error"}

	with patch("ai_ticket_platform.routers.documents.process_document", side_effect=mock_process_side_effect):
		with patch("ai_ticket_platform.routers.documents.initialize_llm_client"):
			async def _run():
				files = [
					{"name": "valid.pdf", "content": BytesIO(b"PDF content"), "type": "application/pdf"},
					{"name": "invalid.txt", "content": BytesIO(b"Text file"), "type": "text/plain"},
				]

				response = await _post_multipart(test_app, "/api/documents/upload", files)

				assert response.status_code == 200
				json_response = response.json()
				assert json_response["total_processed"] == 2
				assert json_response["successful"] == 1
				assert json_response["failed"] == 1

			asyncio.run(_run())


def test_upload_pdf_processing_failure(monkeypatch, test_app: FastAPI):
	"""Test handling of document processing failures."""

	# mock process_document to return failure
	mock_process_result = {
		"filename": "failing.pdf",
		"success": False,
		"error": "Database error: connection failed"
	}

	with patch("ai_ticket_platform.routers.documents.process_document", return_value=mock_process_result):
		with patch("ai_ticket_platform.routers.documents.initialize_llm_client"):
			async def _run():
				files = [{
					"name": "failing.pdf",
					"content": BytesIO(b"PDF content"),
					"type": "application/pdf"
				}]

				response = await _post_multipart(test_app, "/api/documents/upload", files)

				assert response.status_code == 200
				json_response = response.json()
				assert json_response["total_processed"] == 1
				assert json_response["successful"] == 0
				assert json_response["failed"] == 1
				assert json_response["results"][0]["success"] is False
				assert "Database error" in json_response["results"][0]["error"]

			asyncio.run(_run())


def test_upload_case_insensitive_pdf_extension(monkeypatch, test_app: FastAPI):
	"""Test that PDF extension matching is case-insensitive."""

	mock_process_result = {
		"filename": "test.PDF",
		"success": True,
		"area": "Finance",
		"file_id": 1
	}

	with patch("ai_ticket_platform.routers.documents.process_document", return_value=mock_process_result):
		with patch("ai_ticket_platform.routers.documents.initialize_llm_client"):
			async def _run():
				files = [{
					"name": "test.PDF",
					"content": BytesIO(b"PDF content"),
					"type": "application/pdf"
				}]

				response = await _post_multipart(test_app, "/api/documents/upload", files)

				assert response.status_code == 200
				json_response = response.json()
				assert json_response["successful"] == 1
				assert json_response["failed"] == 0

			asyncio.run(_run())
