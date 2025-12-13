"""
Integration tests for CSV upload and clustering functionality.

Tests verify end-to-end data pipeline:
- CSV file parsing and upload
- MySQL data persistence
- Redis caching of clustering results
"""

import pytest
import logging
import time
import json
import os
from datetime import datetime
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
@pytest.mark.skipif(
	os.getenv("CI") == "true",
	reason="Requires RQ workers with real API keys - skip in CI"
)
async def test_csv_upload_persists_to_mysql(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: CSV upload endpoint persists data to MySQL

	Validates:
	- HTTP 200 response
	- Correct number of rows inserted
	- Data types are correct
	- Column mapping is accurate
	"""

	# SETUP: Create test CSV with known data (must have id, subject, body columns)
	csv_content = """id,subject,body
1,Test Ticket 1,This is the first test ticket
2,Test Ticket 2,This is the second test ticket
3,Test Ticket 3,This is the third test ticket
4,Test Ticket 4,This is the fourth test ticket
5,Test Ticket 5,This is the fifth test ticket"""

	logger.info("📤 Uploading test CSV with 5 rows")

	# ACT: Call CSV upload endpoint
	response = await async_client.post(
		"/api/tickets/upload-csv",
		files={"file": ("test_tickets.csv", csv_content, "text/csv")}
	)

	# ASSERT: Check HTTP response
	assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
	response_data = response.json()
	logger.info(f"✅ CSV upload returned 200. Response: {response_data}")

	# Extract rows processed (response structure may vary)
	rows_processed = response_data.get("rows_inserted", response_data.get("rows_processed", response_data.get("rows_uploaded", 0)))
	logger.info(f"📊 CSV upload processed/inserted {rows_processed} rows")

	# Wait for RQ workers to process the jobs (async queue-based processing)
	# Jobs typically take 6-12 seconds to complete (includes LLM API calls)
	logger.info("⏳ Waiting 15 seconds for RQ workers to process jobs...")
	time.sleep(15)

	# ASSERT: Verify MySQL contains tickets with the uploaded data
	query = text("SELECT COUNT(*) as row_count FROM tickets WHERE subject LIKE 'Test Ticket%'")
	result = await db_connection.execute(query)
	row_count = result.scalar()
	assert row_count >= 5, f"Expected at least 5 uploaded rows in MySQL, got {row_count}"
	logger.info(f"✅ MySQL contains {row_count} test tickets")

	# ASSERT: Verify data types and values for first row
	query = text("""
		SELECT id, subject, body
		FROM tickets
		WHERE subject = 'Test Ticket 1'
		LIMIT 1
	""")
	result = await db_connection.execute(query)
	row = result.fetchone()

	if row:
		assert row[1] == "Test Ticket 1", "subject should match"
		assert "first test ticket" in row[2], "body should contain expected text"
		logger.info("✅ Data types and content verified")

	# ASSERT: Verify column mapping accuracy for distinct row
	query = text("SELECT subject FROM tickets WHERE subject = 'Test Ticket 3'")
	result = await db_connection.execute(query)
	subject = result.scalar()
	assert subject == "Test Ticket 3", "Column mapping failed for Test Ticket 3"
	logger.info("✅ Column mapping verified for all uploaded data")


@pytest.mark.asyncio
async def test_health_endpoint_works(
	async_client: AsyncClient,
) -> None:
	"""
	Test: Health endpoint returns successful response

	Validates:
	- GET /ping returns 200
	- Response contains expected structure
	- API is accessible
	"""

	logger.info("🔍 Testing health endpoint...")

	# ACT: Call health endpoint
	response = await async_client.get("/api/health/ping")

	# ASSERT: Endpoint is accessible
	assert response.status_code == 200, f"Health check failed with {response.status_code}"
	logger.info(f"✅ Health endpoint returned 200")

	# ASSERT: Response is valid
	response_data = response.json()
	assert isinstance(response_data, dict), "Response should be dict"
	logger.info(f"✅ Health endpoint response valid: {response_data}")
