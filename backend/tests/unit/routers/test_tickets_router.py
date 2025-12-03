"""Unit tests for tickets router endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi import HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from io import BytesIO

from ai_ticket_platform.routers.tickets import router


@pytest.mark.asyncio
class TestGetTickets:
	"""Test GET /tickets endpoint."""

	async def test_get_tickets_success(self):
		"""Test successful retrieval of tickets list."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_ticket_1 = MagicMock()
		mock_ticket_2 = MagicMock()

		# Tickets router: GET / (index 0), GET /{id} (index 1), POST /upload-csv (index 2), POST /upload-csv-with-pub-sub (index 3)
		get_tickets_endpoint = router.routes[0].endpoint

		mock_response_1 = MagicMock()
		mock_response_1.id = 1
		mock_response_2 = MagicMock()
		mock_response_2.id = 2

		with patch("ai_ticket_platform.routers.tickets.crud_list_tickets", new=AsyncMock(return_value=[mock_ticket_1, mock_ticket_2])):
			with patch("ai_ticket_platform.routers.tickets.crud_count_tickets", new=AsyncMock(return_value=2)):
				with patch("ai_ticket_platform.routers.tickets.TicketResponse.model_validate", side_effect=[mock_response_1, mock_response_2]):
					with patch("ai_ticket_platform.routers.tickets.TicketListResponse") as mock_list_response:
						mock_result = MagicMock()
						mock_list_response.return_value = mock_result

						result = await get_tickets_endpoint(
							skip=0,
							limit=100,
							db=mock_db
						)

						assert result == mock_result
						mock_list_response.assert_called_once_with(
							total=2,
							skip=0,
							limit=100,
							tickets=[mock_response_1, mock_response_2]
						)

	async def test_get_tickets_with_pagination(self):
		"""Test tickets list with custom pagination."""
		mock_db = MagicMock(spec=AsyncSession)

		get_tickets_endpoint = router.routes[0].endpoint

		with patch("ai_ticket_platform.routers.tickets.crud_list_tickets", new=AsyncMock(return_value=[])):
			with patch("ai_ticket_platform.routers.tickets.crud_count_tickets", new=AsyncMock(return_value=0)):
				with patch("ai_ticket_platform.routers.tickets.TicketListResponse") as mock_list_response:
					mock_result = MagicMock()
					mock_list_response.return_value = mock_result

					result = await get_tickets_endpoint(
						skip=10,
						limit=5,
						db=mock_db
					)

					mock_list_response.assert_called_once_with(
						total=0,
						skip=10,
						limit=5,
						tickets=[]
					)


@pytest.mark.asyncio
class TestGetTicketById:
	"""Test GET /tickets/{ticket_id} endpoint."""

	async def test_get_ticket_by_id_success(self):
		"""Test successful retrieval of ticket by ID."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_ticket = MagicMock()

		get_ticket_endpoint = router.routes[1].endpoint

		mock_response = MagicMock()
		mock_response.id = 1

		with patch("ai_ticket_platform.routers.tickets.crud_get_ticket", new=AsyncMock(return_value=mock_ticket)):
			with patch("ai_ticket_platform.routers.tickets.TicketResponse.model_validate", return_value=mock_response):
				result = await get_ticket_endpoint(
					ticket_id=1,
					db=mock_db
				)

				assert result.id == 1

	async def test_get_ticket_by_id_not_found(self):
		"""Test retrieving non-existent ticket raises 404."""
		mock_db = MagicMock(spec=AsyncSession)

		get_ticket_endpoint = router.routes[1].endpoint

		with patch("ai_ticket_platform.routers.tickets.crud_get_ticket", new=AsyncMock(return_value=None)):
			with pytest.raises(HTTPException) as exc_info:
				await get_ticket_endpoint(
					ticket_id=999,
					db=mock_db
				)

			assert exc_info.value.status_code == 404
			assert "Ticket not found" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestUploadTicketsCSV:
	"""Test POST /tickets/upload-csv endpoint."""

	async def test_upload_csv_success(self):
		"""Test successful CSV upload."""
		mock_db = MagicMock(spec=AsyncSession)

		# Create mock file
		csv_content = b"id,subject,body,created_at\n1,Test,Body,2025-01-01"
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "tickets.csv"
		mock_file.content_type = "text/csv"
		mock_file.read = AsyncMock(side_effect=[csv_content, b""])  # First read returns content, second returns empty
		mock_file.seek = AsyncMock()

		upload_endpoint = router.routes[2].endpoint

		mock_result = {
			"total_tickets": 1,
			"successful_imports": 1,
			"failed_imports": 0
		}

		with patch("ai_ticket_platform.routers.tickets.upload_csv_file", new=AsyncMock(return_value=mock_result)):
			with patch("ai_ticket_platform.routers.tickets.CSVUploadResponse") as mock_response:
				mock_response_obj = MagicMock()
				mock_response.return_value = mock_response_obj

				result = await upload_endpoint(
					file=mock_file,
					db=mock_db
				)

				assert result == mock_response_obj
				mock_file.seek.assert_called_once_with(0)

	async def test_upload_csv_invalid_extension(self):
		"""Test CSV upload with invalid file extension."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "tickets.txt"

		upload_endpoint = router.routes[2].endpoint

		with pytest.raises(HTTPException) as exc_info:
			await upload_endpoint(
				file=mock_file,
				db=mock_db
			)

		assert exc_info.value.status_code == 400
		assert "Only CSV files are allowed" in str(exc_info.value.detail)

	async def test_upload_csv_no_filename(self):
		"""Test CSV upload with no filename."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = None

		upload_endpoint = router.routes[2].endpoint

		with pytest.raises(HTTPException) as exc_info:
			await upload_endpoint(
				file=mock_file,
				db=mock_db
			)

		assert exc_info.value.status_code == 400
		assert "Only CSV files are allowed" in str(exc_info.value.detail)

	async def test_upload_csv_invalid_content_type(self):
		"""Test CSV upload with invalid content type."""
		mock_db = MagicMock(spec=AsyncSession)

		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "tickets.csv"
		mock_file.content_type = "application/json"

		upload_endpoint = router.routes[2].endpoint

		with pytest.raises(HTTPException) as exc_info:
			await upload_endpoint(
				file=mock_file,
				db=mock_db
			)

		assert exc_info.value.status_code == 400
		assert "Invalid content type" in str(exc_info.value.detail)

	async def test_upload_csv_file_too_large(self):
		"""Test CSV upload exceeding size limit."""
		mock_db = MagicMock(spec=AsyncSession)

		# Create file larger than 10MB
		large_content = b"x" * (11 * 1024 * 1024)  # 11MB

		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "large_tickets.csv"
		mock_file.content_type = "text/csv"
		mock_file.read = AsyncMock(side_effect=[large_content])

		upload_endpoint = router.routes[2].endpoint

		with pytest.raises(HTTPException) as exc_info:
			await upload_endpoint(
				file=mock_file,
				db=mock_db
			)

		assert exc_info.value.status_code == 400
		assert "File size exceeds 10MB limit" in str(exc_info.value.detail)

	async def test_upload_csv_value_error(self):
		"""Test CSV upload with ValueError from processing."""
		mock_db = MagicMock(spec=AsyncSession)

		csv_content = b"invalid,csv,data"
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "tickets.csv"
		mock_file.content_type = "text/csv"
		mock_file.read = AsyncMock(side_effect=[csv_content, b""])
		mock_file.seek = AsyncMock()

		upload_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.tickets.upload_csv_file", new=AsyncMock(side_effect=ValueError("Invalid CSV format"))):
			with pytest.raises(HTTPException) as exc_info:
				await upload_endpoint(
					file=mock_file,
					db=mock_db
				)

			assert exc_info.value.status_code == 400
			assert "Invalid CSV format" in str(exc_info.value.detail)

	async def test_upload_csv_generic_exception(self):
		"""Test CSV upload with generic exception."""
		mock_db = MagicMock(spec=AsyncSession)

		csv_content = b"id,subject,body\n1,Test,Body"
		mock_file = MagicMock(spec=UploadFile)
		mock_file.filename = "tickets.csv"
		mock_file.content_type = "text/csv"
		mock_file.read = AsyncMock(side_effect=[csv_content, b""])
		mock_file.seek = AsyncMock()

		upload_endpoint = router.routes[2].endpoint

		with patch("ai_ticket_platform.routers.tickets.upload_csv_file", new=AsyncMock(side_effect=Exception("Database error"))):
			with pytest.raises(HTTPException) as exc_info:
				await upload_endpoint(
					file=mock_file,
					db=mock_db
				)

			assert exc_info.value.status_code == 500
			assert "Error processing CSV" in str(exc_info.value.detail)


@pytest.mark.asyncio
class TestProcessTicketsWithPubSub:
	"""Test POST /tickets/upload-csv-with-pub-sub-model endpoint."""

	async def test_process_tickets_success(self):
		"""Test successful ticket processing with pub/sub model."""
		mock_queue = MagicMock()

		# Mock job objects
		mock_job_1 = MagicMock()
		mock_job_1.id = "job-1"
		mock_job_2 = MagicMock()
		mock_job_2.id = "job-2"
		mock_finalizer_job = MagicMock()
		mock_finalizer_job.id = "finalizer-job"

		mock_queue.enqueue = MagicMock(side_effect=[mock_job_1, mock_job_2, mock_job_1, mock_job_2, mock_job_1, mock_finalizer_job])

		process_endpoint = router.routes[3].endpoint

		result = await process_endpoint(queue=mock_queue)

		assert result["total"] == 5
		assert len(result["tickets"]) == 5
		assert "TICKET-001" in result["tickets"]
		assert "Processing" in result["message"]
		assert mock_queue.enqueue.call_count == 6  # 5 tickets + 1 finalizer

	async def test_process_tickets_queue_exception(self):
		"""Test ticket processing when queue raises exception."""
		mock_queue = MagicMock()
		mock_queue.enqueue = MagicMock(side_effect=Exception("Queue connection failed"))

		process_endpoint = router.routes[3].endpoint

		with pytest.raises(HTTPException) as exc_info:
			await process_endpoint(queue=mock_queue)

		assert exc_info.value.status_code == 500
		assert "Queue connection failed" in str(exc_info.value.detail)
