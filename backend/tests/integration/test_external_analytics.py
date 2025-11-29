"""
Integration tests for External Analytics endpoints (A/B testing tracking).

Tests verify:
- Event collection (impressions, resolutions)
- Analytics data retrieval per intent
- Aggregated analytics totals
- Counter increments in database
"""

import pytest
import logging
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_collect_impression_event(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: POST /api/external/collect records impression events

	Validates:
	- HTTP 200 response
	- Event properly recorded
	- Variant impression counters incremented in database
	"""

	# SETUP: Create test intent
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Creating test intent for analytics")

	await db_connection.execute(
		text(
			"INSERT INTO intents (category, title, description, "
			"variant_a_impressions, variant_b_impressions) "
			"VALUES (:category, :title, :description, :var_a, :var_b)"
		),
		{
			"category": "Test",
			"title": "Analytics Test",
			"description": "Testing analytics",
			"var_a": 0,
			"var_b": 0,
		},
	)
	await db_connection.commit()

	# Get intent ID
	result = await db_connection.execute(
		text("SELECT id FROM intents ORDER BY id DESC LIMIT 1")
	)
	intent_id = result.scalar()
	logger.info(f"📌 Created intent with ID: {intent_id}")

	# ACT: Collect impression event for variant A
	logger.info("📊 Collecting impression event for variant A")
	response = await async_client.post(
		"/api/external/collect",
		json={
			"type": "impression",
			"intent_id": intent_id,
			"variant": "A",
		},
	)

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
	data = response.json()
	assert data.get("success") is True, "Event collection should succeed"

	# Verify database was updated
	result = await db_connection.execute(
		text("SELECT variant_a_impressions FROM intents WHERE id = :id"),
		{"id": intent_id},
	)
	var_a_impressions = result.scalar()
	assert var_a_impressions == 1, f"Expected variant_a_impressions=1, got {var_a_impressions}"

	logger.info("✅ Impression event collection test passed")


@pytest.mark.asyncio
async def test_collect_resolution_event(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: POST /api/external/collect records resolution events

	Validates:
	- HTTP 200 response
	- Resolution event properly recorded
	- Variant resolution counters incremented
	"""

	# SETUP: Create test intent
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Creating test intent for resolution tracking")

	await db_connection.execute(
		text(
			"INSERT INTO intents (category, title, description, "
			"variant_a_resolutions, variant_b_resolutions) "
			"VALUES (:category, :title, :description, :res_a, :res_b)"
		),
		{
			"category": "Test",
			"title": "Resolution Test",
			"description": "Testing resolutions",
			"res_a": 0,
			"res_b": 0,
		},
	)
	await db_connection.commit()

	# Get intent ID
	result = await db_connection.execute(
		text("SELECT id FROM intents ORDER BY id DESC LIMIT 1")
	)
	intent_id = result.scalar()
	logger.info(f"📌 Created intent with ID: {intent_id}")

	# ACT: Collect resolution event for variant B
	logger.info("📊 Collecting resolution event for variant B")
	response = await async_client.post(
		"/api/external/collect",
		json={
			"type": "resolution",
			"intent_id": intent_id,
			"variant": "B",
		},
	)

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
	data = response.json()
	assert data.get("success") is True, "Event collection should succeed"

	# Verify database was updated
	result = await db_connection.execute(
		text("SELECT variant_b_resolutions FROM intents WHERE id = :id"),
		{"id": intent_id},
	)
	var_b_resolutions = result.scalar()
	assert var_b_resolutions == 1, f"Expected variant_b_resolutions=1, got {var_b_resolutions}"

	logger.info("✅ Resolution event collection test passed")


@pytest.mark.asyncio
async def test_get_intent_analytics(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/external/analytics/{intent_id} returns intent analytics

	Validates:
	- HTTP 200 response
	- Returns variant A/B impressions and resolutions
	- Correct counts from database
	"""

	# SETUP: Create test intent with analytics data
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Creating test intent with analytics data")

	await db_connection.execute(
		text(
			"INSERT INTO intents (category, title, description, "
			"variant_a_impressions, variant_b_impressions, "
			"variant_a_resolutions, variant_b_resolutions) "
			"VALUES (:category, :title, :description, :a_imp, :b_imp, :a_res, :b_res)"
		),
		{
			"category": "Test",
			"title": "Analytics Test",
			"description": "Testing analytics",
			"a_imp": 10,
			"b_imp": 8,
			"a_res": 5,
			"b_res": 3,
		},
	)
	await db_connection.commit()

	# Get intent ID
	result = await db_connection.execute(
		text("SELECT id FROM intents ORDER BY id DESC LIMIT 1")
	)
	intent_id = result.scalar()
	logger.info(f"📌 Created intent with ID: {intent_id}")

	# ACT: Get analytics for this intent
	logger.info("📊 Retrieving intent analytics")
	response = await async_client.get(f"/api/external/analytics/{intent_id}")

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
	data = response.json()

	assert "variant_a_impressions" in data, "Missing variant_a_impressions"
	assert "variant_b_impressions" in data, "Missing variant_b_impressions"
	assert "variant_a_resolutions" in data, "Missing variant_a_resolutions"
	assert "variant_b_resolutions" in data, "Missing variant_b_resolutions"

	assert data["variant_a_impressions"] == 10, f"Expected 10, got {data['variant_a_impressions']}"
	assert data["variant_b_impressions"] == 8, f"Expected 8, got {data['variant_b_impressions']}"
	assert data["variant_a_resolutions"] == 5, f"Expected 5, got {data['variant_a_resolutions']}"
	assert data["variant_b_resolutions"] == 3, f"Expected 3, got {data['variant_b_resolutions']}"

	logger.info("✅ Intent analytics retrieval test passed")


@pytest.mark.asyncio
async def test_get_analytics_totals(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/external/analytics/totals returns aggregated analytics

	Validates:
	- HTTP 200 response
	- Returns aggregated A/B testing data across all intents
	- Correct sum of all impressions and resolutions
	"""

	# SETUP: Create multiple intents with analytics data
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Creating multiple intents with analytics data")

	# Intent 1: A=10 impressions, B=8 impressions, A=5 resolutions, B=3 resolutions
	await db_connection.execute(
		text(
			"INSERT INTO intents (category, title, description, "
			"variant_a_impressions, variant_b_impressions, "
			"variant_a_resolutions, variant_b_resolutions) "
			"VALUES (:category, :title, :description, :a_imp, :b_imp, :a_res, :b_res)"
		),
		{
			"category": "Test1",
			"title": "Intent 1",
			"description": "Test intent 1",
			"a_imp": 10,
			"b_imp": 8,
			"a_res": 5,
			"b_res": 3,
		},
	)

	# Intent 2: A=15 impressions, B=12 impressions, A=7 resolutions, B=4 resolutions
	await db_connection.execute(
		text(
			"INSERT INTO intents (category, title, description, "
			"variant_a_impressions, variant_b_impressions, "
			"variant_a_resolutions, variant_b_resolutions) "
			"VALUES (:category, :title, :description, :a_imp, :b_imp, :a_res, :b_res)"
		),
		{
			"category": "Test2",
			"title": "Intent 2",
			"description": "Test intent 2",
			"a_imp": 15,
			"b_imp": 12,
			"a_res": 7,
			"b_res": 4,
		},
	)
	await db_connection.commit()

	logger.info("📊 Retrieving aggregated analytics totals")

	# ACT: Get aggregated totals
	response = await async_client.get("/api/external/analytics/totals")

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
	data = response.json()

	assert "variant_a_impressions" in data, "Missing variant_a_impressions in totals"
	assert "variant_b_impressions" in data, "Missing variant_b_impressions in totals"
	assert "variant_a_resolutions" in data, "Missing variant_a_resolutions in totals"
	assert "variant_b_resolutions" in data, "Missing variant_b_resolutions in totals"

	# Should be sum of both intents
	assert data["variant_a_impressions"] == 25, f"Expected 25 total, got {data['variant_a_impressions']}"
	assert data["variant_b_impressions"] == 20, f"Expected 20 total, got {data['variant_b_impressions']}"
	assert data["variant_a_resolutions"] == 12, f"Expected 12 total, got {data['variant_a_resolutions']}"
	assert data["variant_b_resolutions"] == 7, f"Expected 7 total, got {data['variant_b_resolutions']}"

	logger.info("✅ Analytics totals retrieval test passed")
