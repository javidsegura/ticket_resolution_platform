"""Unit tests for tickets router endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestGetTickets:
	"""Test GET /tickets endpoint."""

	async def test_get_tickets_success(self):
		"""Test successfully retrieving paginated list of tickets."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)

		# Mock tickets
		mock_ticket_1 = MagicMock()
		mock_ticket_1.id = 1
		mock_ticket_1.subject = "Test Ticket 1"
		mock_ticket_1.body = "Test body 1"
		mock_ticket_1.intent_id = None
		mock_ticket_1.created_at = "2025-01-01T00:00:00"

		mock_ticket_2 = MagicMock()
		mock_ticket_2.id = 2
		mock_ticket_2.subject = "Test Ticket 2"
		mock_ticket_2.body = "Test body 2"
		mock_ticket_2.intent_id = None
		mock_ticket_2.created_at = "2025-01-01T00:00:00"

		async def mock_get_db():
			yield mock_db

		with patch("ai_ticket_platform.routers.tickets.crud_list_tickets", new=AsyncMock(return_value=[mock_ticket_1, mock_ticket_2])):
			with patch("ai_ticket_platform.routers.tickets.crud_count_tickets", new=AsyncMock(return_value=2)):
				with patch("ai_ticket_platform.routers.tickets.get_db", mock_get_db):
					async with AsyncClient(
						transport=ASGITransport(app=app),
						base_url="http://test"
					) as client:
						response = await client.get("/api/tickets/")

						assert response.status_code == 200
						data = response.json()
						assert data["total"] == 2
						assert data["skip"] == 0
						assert data["limit"] == 100
						assert len(data["tickets"]) == 2
						assert data["tickets"][0]["id"] == 1
						assert data["tickets"][0]["subject"] == "Test Ticket 1"

	async def test_get_tickets_with_pagination(self):
		"""Test retrieving tickets with custom pagination."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)

		async def mock_get_db():
			yield mock_db

		with patch("ai_ticket_platform.routers.tickets.crud_list_tickets", new=AsyncMock(return_value=[])):
			with patch("ai_ticket_platform.routers.tickets.crud_count_tickets", new=AsyncMock(return_value=100)):
				with patch("ai_ticket_platform.routers.tickets.get_db", mock_get_db):
					async with AsyncClient(
						transport=ASGITransport(app=app),
						base_url="http://test"
					) as client:
						response = await client.get("/api/tickets/?skip=10&limit=20")

						assert response.status_code == 200
						data = response.json()
						assert data["total"] == 100
						assert data["skip"] == 10
						assert data["limit"] == 20

	async def test_get_tickets_empty_list(self):
		"""Test retrieving tickets when none exist."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)

		async def mock_get_db():
			yield mock_db

		with patch("ai_ticket_platform.routers.tickets.crud_list_tickets", new=AsyncMock(return_value=[])):
			with patch("ai_ticket_platform.routers.tickets.crud_count_tickets", new=AsyncMock(return_value=0)):
				with patch("ai_ticket_platform.routers.tickets.get_db", mock_get_db):
					async with AsyncClient(
						transport=ASGITransport(app=app),
						base_url="http://test"
					) as client:
						response = await client.get("/api/tickets/")

						assert response.status_code == 200
						data = response.json()
						assert data["total"] == 0
						assert len(data["tickets"]) == 0


@pytest.mark.asyncio
class TestGetTicketById:
	"""Test GET /tickets/{ticket_id} endpoint."""

	async def test_get_ticket_by_id_success(self):
		"""Test successfully retrieving a single ticket."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)

		mock_ticket = MagicMock()
		mock_ticket.id = 1
		mock_ticket.subject = "Test Ticket"
		mock_ticket.body = "Test body"
		mock_ticket.intent_id = None
		mock_ticket.created_at = "2025-01-01T00:00:00"

		async def mock_get_db():
			yield mock_db

		with patch("ai_ticket_platform.routers.tickets.crud_get_ticket", new=AsyncMock(return_value=mock_ticket)):
			with patch("ai_ticket_platform.routers.tickets.get_db", mock_get_db):
				async with AsyncClient(
					transport=ASGITransport(app=app),
					base_url="http://test"
				) as client:
					response = await client.get("/api/tickets/1")

					assert response.status_code == 200
					data = response.json()
					assert data["id"] == 1
					assert data["subject"] == "Test Ticket"
					assert data["body"] == "Test body"

	async def test_get_ticket_by_id_not_found(self):
		"""Test retrieving ticket that doesn't exist."""
		from ai_ticket_platform.main import app

		mock_db = MagicMock(spec=AsyncSession)

		async def mock_get_db():
			yield mock_db

		with patch("ai_ticket_platform.routers.tickets.crud_get_ticket", new=AsyncMock(return_value=None)):
			with patch("ai_ticket_platform.routers.tickets.get_db", mock_get_db):
				async with AsyncClient(
					transport=ASGITransport(app=app),
					base_url="http://test"
				) as client:
					response = await client.get("/api/tickets/999")

					assert response.status_code == 404
					assert "Ticket not found" in response.json()["detail"]


@pytest.mark.asyncio
class TestUploadCSV:
	"""Test POST /tickets/upload-csv endpoint."""

	async def test_upload_csv_invalid_file_type(self):
		"""Test uploading non-CSV file is rejected."""
		from ai_ticket_platform.main import app

		mock_queue = MagicMock()

		def mock_get_queue():
			return mock_queue

		with patch("ai_ticket_platform.routers.tickets.get_queue", mock_get_queue):
			async with AsyncClient(
				transport=ASGITransport(app=app),
				base_url="http://test"
			) as client:
				files = {"file": ("test.txt", b"content", "text/plain")}
				response = await client.post("/api/tickets/upload-csv", files=files)

				assert response.status_code == 400
				assert "Only CSV files are allowed" in response.json()["detail"]

	async def test_upload_csv_invalid_content_type(self):
		"""Test uploading file with invalid content type."""
		from ai_ticket_platform.main import app

		mock_queue = MagicMock()

		def mock_get_queue():
			return mock_queue

		with patch("ai_ticket_platform.routers.tickets.get_queue", mock_get_queue):
			async with AsyncClient(
				transport=ASGITransport(app=app),
				base_url="http://test"
			) as client:
				files = {"file": ("test.csv", b"content", "application/json")}
				response = await client.post("/api/tickets/upload-csv", files=files)

				assert response.status_code == 400
				assert "Invalid content type" in response.json()["detail"]

	async def test_upload_csv_file_too_large(self):
		"""Test uploading file exceeding size limit."""
		from ai_ticket_platform.main import app

		mock_queue = MagicMock()

		def mock_get_queue():
			return mock_queue

		# Create a file larger than 10MB
		large_content = b"x" * (11 * 1024 * 1024)  # 11MB

		with patch("ai_ticket_platform.routers.tickets.get_queue", mock_get_queue):
			async with AsyncClient(
				transport=ASGITransport(app=app),
				base_url="http://test"
			) as client:
				files = {"file": ("test.csv", large_content, "text/csv")}
				response = await client.post("/api/tickets/upload-csv", files=files)

				assert response.status_code == 400
				assert "File size exceeds 10MB limit" in response.json()["detail"]
