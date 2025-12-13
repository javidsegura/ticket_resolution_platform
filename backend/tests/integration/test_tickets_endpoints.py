"""
Integration tests for Ticket endpoints (GET /api/tickets, GET /api/tickets/{id}).

Tests verify:
- Ticket list retrieval with pagination
- Individual ticket retrieval by ID
- Proper HTTP status codes and response schemas
- CSV upload -> ticket retrieval flow
"""

import pytest
import logging
import time
import os
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_get_tickets_empty_list(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/tickets returns empty list when no tickets exist

	Validates:
	- HTTP 200 response
	- Response structure contains total, skip, limit, tickets
	- Empty tickets array
	"""

	# SETUP: Ensure database is clean
	await db_connection.execute(text("DELETE FROM tickets"))
	await db_connection.commit()

	logger.info("📋 Testing GET /api/tickets on empty database")

	# ACT: Get tickets
	response = await async_client.get("/api/tickets")

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	data = response.json()

	assert "total" in data, "Response missing 'total' field"
	assert "tickets" in data, "Response missing 'tickets' field"
	assert "skip" in data, "Response missing 'skip' field"
	assert "limit" in data, "Response missing 'limit' field"

	assert data["total"] == 0, f"Expected 0 tickets, got {data['total']}"
	assert data["tickets"] == [], f"Expected empty list, got {data['tickets']}"
	assert data["skip"] == 0, f"Expected skip=0, got {data['skip']}"
	assert data["limit"] == 100, f"Expected default limit=100, got {data['limit']}"

	logger.info("✅ GET /api/tickets empty list test passed")


@pytest.mark.asyncio
async def test_get_tickets_pagination(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/tickets pagination with skip and limit parameters

	Validates:
	- Correct number of results returned
	- Skip parameter works correctly
	- Limit parameter works correctly
	- Total count is accurate
	"""

	# SETUP: Clear and insert test data
	await db_connection.execute(text("DELETE FROM tickets"))
	await db_connection.commit()

	logger.info("📤 Inserting 25 test tickets for pagination test")

	# Insert 25 test tickets
	for i in range(1, 26):
		await db_connection.execute(
			text(
				"INSERT INTO tickets (subject, body) VALUES (:subject, :body)"
			),
			{"subject": f"Ticket {i}", "body": f"Body for ticket {i}"},
		)
	await db_connection.commit()

	logger.info("📋 Testing pagination parameters")

	# ACT & ASSERT: Test default pagination (skip=0, limit=100)
	response = await async_client.get("/api/tickets")
	assert response.status_code == 200
	data = response.json()
	assert data["total"] == 25
	assert len(data["tickets"]) == 25
	assert data["skip"] == 0
	assert data["limit"] == 100

	# ACT & ASSERT: Test with custom limit
	response = await async_client.get("/api/tickets?limit=10")
	assert response.status_code == 200
	data = response.json()
	assert data["total"] == 25
	assert len(data["tickets"]) == 10
	assert data["limit"] == 10
	assert data["skip"] == 0

	# ACT & ASSERT: Test with skip
	response = await async_client.get("/api/tickets?skip=10&limit=10")
	assert response.status_code == 200
	data = response.json()
	assert data["total"] == 25
	assert len(data["tickets"]) == 10
	assert data["skip"] == 10
	first_ticket_id = data["tickets"][0]["id"]

	# ACT & ASSERT: Get second page and verify different tickets
	response_page1 = await async_client.get("/api/tickets?skip=0&limit=10")
	first_page_last_id = response_page1.json()["tickets"][-1]["id"]
	assert first_ticket_id != first_page_last_id, "Pagination should return different tickets"

	logger.info("✅ Pagination test passed")


@pytest.mark.asyncio
async def test_get_ticket_by_id_success(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/tickets/{ticket_id} returns correct ticket

	Validates:
	- HTTP 200 response for valid ticket
	- Response contains all required fields
	- Correct ticket data returned
	"""

	# SETUP: Clear and insert test ticket
	await db_connection.execute(text("DELETE FROM tickets"))
	await db_connection.commit()

	logger.info("📤 Inserting test ticket")

	await db_connection.execute(
		text(
			"INSERT INTO tickets (subject, body) VALUES (:subject, :body)"
		),
		{
			"subject": "Test Ticket",
			"body": "This is a test ticket body",
		},
	)
	await db_connection.commit()

	# Get the ticket ID (MySQL auto-increment)
	result = await db_connection.execute(
		text("SELECT id FROM tickets ORDER BY id DESC LIMIT 1")
	)
	ticket_id = result.scalar()
	logger.info(f"📌 Created ticket with ID: {ticket_id}")

	# ACT: Get the ticket
	response = await async_client.get(f"/api/tickets/{ticket_id}")

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	data = response.json()

	assert "id" in data, "Response missing 'id'"
	assert "subject" in data, "Response missing 'subject'"
	assert "body" in data, "Response missing 'body'"

	assert data["id"] == ticket_id, f"Expected ID {ticket_id}, got {data['id']}"
	assert (
		data["subject"] == "Test Ticket"
	), f"Expected 'Test Ticket', got {data['subject']}"
	assert (
		data["body"] == "This is a test ticket body"
	), f"Expected correct body, got {data['body']}"

	logger.info("✅ GET /api/tickets/{id} success test passed")


@pytest.mark.asyncio
async def test_get_ticket_by_id_not_found(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/tickets/{ticket_id} returns 404 for non-existent ticket

	Validates:
	- HTTP 404 status code
	- Proper error message
	"""

	logger.info("📋 Testing GET /api/tickets/{id} with non-existent ID")

	# ACT: Get non-existent ticket
	response = await async_client.get("/api/tickets/999999")

	# ASSERT
	assert response.status_code == 404, f"Expected 404, got {response.status_code}"
	data = response.json()
	assert "detail" in data, "Response missing error detail"

	logger.info("✅ GET /api/tickets/{id} 404 test passed")


@pytest.mark.asyncio
@pytest.mark.skipif(
	os.getenv("CI") == "true",
	reason="Requires RQ workers with real API keys - skip in CI"
)
async def test_csv_upload_then_get_tickets(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: Full flow - Upload CSV then retrieve tickets via GET endpoint

	Validates:
	- CSV upload creates tickets in database
	- GET /api/tickets retrieves the uploaded tickets
	- Data consistency end-to-end
	"""

	# SETUP: Clear database
	await db_connection.execute(text("DELETE FROM tickets"))
	await db_connection.commit()

	logger.info("📤 Uploading CSV file")

	# Create test CSV with proper format
	csv_content = """subject,body
Test Ticket 1,This is the first test ticket
Test Ticket 2,This is the second test ticket
Test Ticket 3,This is the third test ticket"""

	# ACT: Upload CSV
	response = await async_client.post(
		"/api/tickets/upload-csv",
		files={"file": ("test.csv", csv_content.encode(), "text/csv")},
	)

	logger.info(f"📤 CSV upload response: {response.status_code}")
	assert response.status_code == 200, f"CSV upload failed: {response.text}"

	# Wait for RQ workers to process the jobs (async queue-based processing)
	# Jobs typically take 6-12 seconds to complete (includes LLM API calls)
	logger.info("⏳ Waiting 15 seconds for RQ workers to process jobs...")
	time.sleep(15)

	# ACT: Get tickets from API
	response = await async_client.get("/api/tickets")

	# ASSERT
	assert response.status_code == 200
	data = response.json()

	assert data["total"] >= 3, f"Expected at least 3 tickets, got {data['total']}"
	assert len(data["tickets"]) >= 3, "Should have at least 3 tickets in response"

	# Verify uploaded data is present
	subjects = [t["subject"] for t in data["tickets"]]
	assert "Test Ticket 1" in subjects, "Uploaded ticket 1 not found"
	assert "Test Ticket 2" in subjects, "Uploaded ticket 2 not found"
	assert "Test Ticket 3" in subjects, "Uploaded ticket 3 not found"

	logger.info("✅ CSV upload → GET /api/tickets flow test passed")
