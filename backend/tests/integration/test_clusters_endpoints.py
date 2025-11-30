"""
Integration tests for Cluster endpoints (GET /api/intents mapped as clusters).

Tests verify that clusters (implemented as intents) support:
- Cluster list retrieval with pagination
- Individual cluster retrieval by ID
- Cluster filtering by processing status
- Cluster A/B testing metrics retrieval
- Proper HTTP status codes and response schemas
"""

import pytest
import logging
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_list_clusters_empty(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/intents returns empty list when no clusters exist

	Validates:
	- HTTP 200 response
	- Empty clusters array
	- Response is a valid list
	"""

	# SETUP: Ensure intents (clusters) table is clean
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📋 Testing GET /api/intents on empty database (no clusters)")

	# ACT: Get clusters
	response = await async_client.get("/api/intents")

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	data = response.json()

	assert isinstance(data, list), "Expected list response"
	assert len(data) == 0, f"Expected empty list, got {len(data)} items"

	logger.info("✅ GET /api/intents (clusters) empty list test passed")


@pytest.mark.asyncio
async def test_list_clusters_pagination(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/intents pagination for cluster listing

	Validates:
	- Correct number of clusters returned per page
	- Skip parameter works correctly
	- Limit parameter works correctly
	"""

	# SETUP: Clear and insert test clusters
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Inserting 12 test clusters for pagination test")

	# Insert 12 test clusters (intents)
	for i in range(1, 13):
		await db_connection.execute(
			text(
				"INSERT INTO intents (name, area, is_processed) "
				"VALUES (:name, :area, :is_processed)"
			),
			{
				"name": f"Cluster {i}",
				"area": f"Topic Area {i}",
				"is_processed": i > 6,  # First 6 unprocessed, last 6 processed
			},
		)
	await db_connection.commit()

	logger.info("📋 Testing cluster pagination parameters")

	# ACT & ASSERT: Test default pagination (skip=0, limit=100)
	response = await async_client.get("/api/intents")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 12, f"Expected 12 clusters, got {len(data)}"

	# ACT & ASSERT: Test with custom limit
	response = await async_client.get("/api/intents?limit=4")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 4, f"Expected 4 clusters, got {len(data)}"

	# ACT & ASSERT: Test with skip
	response = await async_client.get("/api/intents?skip=8&limit=4")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 4, f"Expected 4 clusters, got {len(data)}"

	logger.info("✅ Cluster pagination test passed")


@pytest.mark.asyncio
async def test_get_cluster_by_id(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/intents/{intent_id} returns correct cluster

	Validates:
	- HTTP 200 response for valid cluster
	- Response contains all required cluster fields
	- Correct cluster data returned
	"""

	# SETUP: Clear and insert test cluster
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Inserting test cluster")

	await db_connection.execute(
		text(
			"INSERT INTO intents (name, area, is_processed, "
			"variant_a_impressions, variant_b_impressions, "
			"variant_a_resolutions, variant_b_resolutions) "
			"VALUES (:name, :area, :is_processed, :var_a_imp, :var_b_imp, :var_a_res, :var_b_res)"
		),
		{
			"name": "Authentication Issues",
			"area": "Security",
			"is_processed": True,
			"var_a_imp": 150,
			"var_b_imp": 160,
			"var_a_res": 120,
			"var_b_res": 135,
		},
	)
	await db_connection.commit()

	# Get the cluster ID
	result = await db_connection.execute(
		text("SELECT id FROM intents ORDER BY id DESC LIMIT 1")
	)
	cluster_id = result.scalar()
	logger.info(f"📌 Created cluster with ID: {cluster_id}")

	# ACT: Get the cluster
	response = await async_client.get(f"/api/intents/{cluster_id}")

	# ASSERT
	assert response.status_code == 200, f"Expected 200, got {response.status_code}"
	data = response.json()

	# Verify cluster fields exist
	assert "id" in data, "Response missing 'id'"
	assert "name" in data, "Response missing 'name'"
	assert "area" in data, "Response missing 'area'"
	assert "is_processed" in data, "Response missing 'is_processed'"

	# Verify cluster A/B testing metrics exist
	assert "variant_a_impressions" in data, "Response missing 'variant_a_impressions'"
	assert "variant_b_impressions" in data, "Response missing 'variant_b_impressions'"
	assert "variant_a_resolutions" in data, "Response missing 'variant_a_resolutions'"
	assert "variant_b_resolutions" in data, "Response missing 'variant_b_resolutions'"

	# Verify correct data
	assert data["id"] == cluster_id, f"Expected ID {cluster_id}, got {data['id']}"
	assert data["name"] == "Authentication Issues", f"Expected 'Authentication Issues', got {data['name']}"
	assert data["area"] == "Security", f"Expected 'Security', got {data['area']}"
	assert data["is_processed"] is True, f"Expected is_processed=True, got {data['is_processed']}"
	assert data["variant_a_impressions"] == 150, f"Expected 150 impressions, got {data['variant_a_impressions']}"

	logger.info("✅ GET /api/intents/{id} (cluster) success test passed")


@pytest.mark.asyncio
async def test_get_cluster_by_id_not_found(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: GET /api/intents/{intent_id} returns 404 for non-existent cluster

	Validates:
	- HTTP 404 status code
	- Proper error response
	"""

	logger.info("📋 Testing GET /api/intents/{id} with non-existent cluster ID")

	# ACT: Get non-existent cluster
	response = await async_client.get("/api/intents/999999")

	# ASSERT
	assert response.status_code == 404, f"Expected 404, got {response.status_code}"
	data = response.json()
	assert "detail" in data, "Response missing error detail"

	logger.info("✅ GET /api/intents/{id} 404 test passed")


@pytest.mark.asyncio
async def test_filter_clusters_by_processed_status(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: Filter clusters by is_processed status

	Validates:
	- GET /api/intents?is_processed=true returns only processed clusters
	- GET /api/intents?is_processed=false returns only unprocessed clusters
	"""

	# SETUP: Clear and insert mixed clusters
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Inserting processed and unprocessed clusters")

	# Insert 4 processed clusters
	for i in range(1, 5):
		await db_connection.execute(
			text(
				"INSERT INTO intents (name, area, is_processed) "
				"VALUES (:name, :area, :is_processed)"
			),
			{
				"name": f"Resolved Cluster {i}",
				"area": f"Area {i}",
				"is_processed": True,
			},
		)

	# Insert 4 unprocessed clusters
	for i in range(1, 5):
		await db_connection.execute(
			text(
				"INSERT INTO intents (name, area, is_processed) "
				"VALUES (:name, :area, :is_processed)"
			),
			{
				"name": f"Pending Cluster {i}",
				"area": f"Area {i+10}",
				"is_processed": False,
			},
		)
	await db_connection.commit()

	logger.info("📋 Testing cluster filter by is_processed=true")

	# ACT & ASSERT: Get processed clusters
	response = await async_client.get("/api/intents?is_processed=true")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 4, f"Expected 4 processed clusters, got {len(data)}"
	for cluster in data:
		assert cluster["is_processed"] is True, f"Found unprocessed cluster in processed results: {cluster}"

	logger.info("📋 Testing cluster filter by is_processed=false")

	# ACT & ASSERT: Get unprocessed clusters
	response = await async_client.get("/api/intents?is_processed=false")
	assert response.status_code == 200
	data = response.json()
	assert isinstance(data, list)
	assert len(data) == 4, f"Expected 4 unprocessed clusters, got {len(data)}"
	for cluster in data:
		assert cluster["is_processed"] is False, f"Found processed cluster in unprocessed results: {cluster}"

	logger.info("✅ Filter by is_processed test passed")


@pytest.mark.asyncio
async def test_cluster_ab_testing_metrics(
	async_client: AsyncClient,
	db_connection: AsyncSession,
) -> None:
	"""
	Test: Cluster A/B testing metrics are correctly returned

	Validates:
	- Cluster contains A/B variant impressions
	- Cluster contains A/B variant resolutions
	- Metrics can be used to calculate conversion rates
	"""

	# SETUP: Create test cluster with A/B metrics
	await db_connection.execute(text("DELETE FROM intents"))
	await db_connection.commit()

	logger.info("📤 Creating cluster with A/B testing metrics")

	await db_connection.execute(
		text(
			"INSERT INTO intents (name, area, is_processed, "
			"variant_a_impressions, variant_b_impressions, "
			"variant_a_resolutions, variant_b_resolutions) "
			"VALUES (:name, :area, :is_processed, :var_a_imp, :var_b_imp, :var_a_res, :var_b_res)"
		),
		{
			"name": "Payment Processing",
			"area": "Billing",
			"is_processed": True,
			"var_a_imp": 200,
			"var_b_imp": 210,
			"var_a_res": 160,
			"var_b_res": 180,
		},
	)
	await db_connection.commit()

	# Get the cluster ID
	result = await db_connection.execute(
		text("SELECT id FROM intents ORDER BY id DESC LIMIT 1")
	)
	cluster_id = result.scalar()
	logger.info(f"📌 Created cluster with ID: {cluster_id}")

	# ACT: Get cluster
	response = await async_client.get(f"/api/intents/{cluster_id}")

	# ASSERT
	assert response.status_code == 200
	cluster = response.json()

	# Verify A/B metrics
	assert cluster["variant_a_impressions"] == 200
	assert cluster["variant_b_impressions"] == 210
	assert cluster["variant_a_resolutions"] == 160
	assert cluster["variant_b_resolutions"] == 180

	# Verify we can calculate conversion rates
	var_a_conversion = cluster["variant_a_resolutions"] / cluster["variant_a_impressions"]
	var_b_conversion = cluster["variant_b_resolutions"] / cluster["variant_b_impressions"]

	assert var_a_conversion == 0.8, f"Expected Variant A conversion 0.8, got {var_a_conversion}"
	assert abs(var_b_conversion - (180/210)) < 0.01, f"Expected Variant B conversion ~0.857, got {var_b_conversion}"

	logger.info(f"✅ A/B metrics test passed - Variant A: {var_a_conversion:.2%}, Variant B: {var_b_conversion:.2%}")
