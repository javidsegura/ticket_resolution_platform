"""
Integration tests for Intent endpoints (GET /api/intents, GET /api/intents/{id}).

Tests verify:
- Intent list retrieval with pagination and filtering
- Individual intent retrieval by ID
- Filtering by is_processed status
- Proper HTTP status codes and response schemas
"""

import pytest
import logging
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_list_intents_empty(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/intents returns empty list when no intents exist

	Validates:
	- HTTP 200 response
	- Response structure with total, skip, limit
	- Empty intents array
	"""

	# SETUP: Ensure intents table is clean
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📋 Testing GET /api/intents on empty database")

	# ACT: Get intents
	response = await async_client.get("/api/intents")

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	data = response.json()

	assert isinstance(data, list), "Expected list response"
	assert len(data) == 0, f"Expected empty list, got {len(data)} items"

	logger.info("✅ GET /api/intents empty list test passed")


@pytest.mark.asyncio
async def test_list_intents_pagination(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/intents pagination with skip and limit parameters

	Validates:
	- Correct number of results returned
	- Skip parameter works correctly
	- Limit parameter works correctly
	- Total count via response length
	"""

	# SETUP: Clear and insert test intents
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Inserting 15 test intents for pagination test")

	# Insert 15 test intents
	for i in range(1, 16):
		await db_connection.execute(
			text(
				"INSERT INTO intents (category, title, description, is_processed) "
				"VALUES (:category, :title, :description, :is_processed)"
			),
			{
				"category": f"Category {i}",
				"title": f"Intent {i}",
				"description": f"Description for intent {i}",
				"is_processed": i % 2 == 0,  # Half processed, half not
			},
		)
	await db_connection.commit()

	logger.info("📋 Testing pagination parameters")

	# ACT & ASSERT: Test default pagination (skip=0, limit=100)
	response = await async_client.get("/api/intents")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 15

	# ACT & ASSERT: Test with custom limit
	response = await async_client.get("/api/intents?limit=5")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 5

	# ACT & ASSERT: Test with skip
	response = await async_client.get("/api/intents?skip=10&limit=5")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 5

	logger.info("✅ Pagination test passed")


@pytest.mark.asyncio
async def test_get_intent_by_id(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/intents/{intent_id} returns correct intent

	Validates:
	- HTTP 200 response for valid intent
	- Response contains all required fields
	- Correct intent data returned
	"""

	# SETUP: Clear and insert test intent
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Inserting test intent")

	await db_connection.execute(
		text(
			"INSERT INTO intents (category, title, description, is_processed) "
			"VALUES (:category, :title, :description, :is_processed)"
		),
		{
			"category": "Test Category",
			"title": "Test Intent",
			"description": "This is a test intent",
			"is_processed": False,
		},
	)
	await db_connection.commit()

	# Get the intent ID
	result = await db_connection.execute(
		text("SELECT id FROM intents ORDER BY id DESC LIMIT 1")
	)
	intent_id = result.scalar()
	logger.info(f"📌 Created intent with ID: {intent_id}")

	# ACT: Get the intent
	response = await async_client.get(f"/api/intents/{intent_id}")

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	data = response.json()

	assert "id" in data, "Response missing 'id'"
	assert "title" in data, "Response missing 'title'"
	assert "description" in data, "Response missing 'description'"
	assert "is_processed" in data, "Response missing 'is_processed'"

	assert data["id"] == intent_id, f"Expected ID {intent_id}, got {data['id']}"
	assert data["title"] == "Test Intent", f"Expected 'Test Intent', got {data['title']}"
	assert data["is_processed"] is False, f"Expected is_processed=False, got {data['is_processed']}"

	logger.info("✅ GET /api/intents/{id} success test passed")


@pytest.mark.asyncio
async def test_get_intent_by_id_not_found(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/intents/{intent_id} returns 404 for non-existent intent

	Validates:
	- HTTP 404 status code
	- Proper error message
	"""

	logger.info("📋 Testing GET /api/intents/{id} with non-existent ID")

	# ACT: Get non-existent intent
	response = await async_client.get("/api/intents/999999")

	# ASSERT
	assert response.status_code == 404, f"Expected 404, got {response.status_code}"
	data = response.json()
	assert "detail" in data, "Response missing error detail"

	logger.info("✅ GET /api/intents/{id} 404 test passed")


@pytest.mark.asyncio
async def test_filter_intents_by_processed_status(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: Filter intents by is_processed status

	Validates:
	- GET /api/intents?is_processed=true returns only processed intents
	- GET /api/intents?is_processed=false returns only unprocessed intents
	- Filtering works correctly across database
	"""

	# SETUP: Clear and insert mixed intents
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Inserting processed and unprocessed intents")

	# Insert 5 processed and 5 unprocessed intents
	for i in range(1, 6):
		await db_connection.execute(
			text(
				"INSERT INTO intents (category, title, description, is_processed) "
				"VALUES (:category, :title, :description, :is_processed)"
			),
			{
				"category": f"Processed {i}",
				"title": f"Processed Intent {i}",
				"description": f"This intent is processed",
				"is_processed": True,
			},
		)

		await db_connection.execute(
			text(
				"INSERT INTO intents (category, title, description, is_processed) "
				"VALUES (:category, :title, :description, :is_processed)"
			),
			{
				"category": f"Unprocessed {i}",
				"title": f"Unprocessed Intent {i}",
				"description": f"This intent is not processed",
				"is_processed": False,
			},
		)
	await db_connection.commit()

	logger.info("📋 Testing filter by is_processed=true")

	# ACT & ASSERT: Get processed intents
	response = await async_client.get("/api/intents?is_processed=true")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 5, f"Expected 5 processed intents, got {len(data)}"
	for intent in data:
		assert intent["is_processed"] is True, f"Found unprocessed intent in processed results: {intent}"

	logger.info("📋 Testing filter by is_processed=false")

	# ACT & ASSERT: Get unprocessed intents
	response = await async_client.get("/api/intents?is_processed=false")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 5, f"Expected 5 unprocessed intents, got {len(data)}"
	for intent in data:
		assert intent["is_processed"] is False, f"Found processed intent in unprocessed results: {intent}"

	logger.info("✅ Filter by is_processed test passed")
