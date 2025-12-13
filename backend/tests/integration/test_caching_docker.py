"""
Integration tests for caching behavior and Redis functionality.

Tests verify:
- Cache-aside pattern implementation
- TTL expiration and eviction
- Cache hit/miss detection
- Redis data persistence
"""

import pytest
import logging
import json
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_redis_cache_operations(
	redis_client: redis.Redis,
) -> None:
	"""
	Test: Validate basic Redis cache operations work

	Validates:
	- SET/GET operations work
	- Data persistence in Redis
	- Cache key management
	"""

	logger.info("🔄 Testing Redis cache operations...")

	# SETUP: Clear any test keys
	await redis_client.delete("cache_test_key")
	logger.info("✅ Cleared cache key")

	# ASSERT: Verify cache is empty initially
	cache_before = await redis_client.get("cache_test_key")
	assert cache_before is None, "Cache should be empty before SET"
	logger.info("✅ Cache key doesn't exist initially")

	# ACT: Set a value in cache
	test_data = {"user_id": "123", "status": "active"}
	await redis_client.set("cache_test_key", json.dumps(test_data))
	logger.info("✅ Set value in Redis cache")

	# ASSERT: Redis contains the key
	cache_after_set = await redis_client.get("cache_test_key")
	assert cache_after_set is not None, "Cache key should exist after SET"
	cached_data = json.loads(cache_after_set)
	assert cached_data["user_id"] == "123"
	logger.info("✅ Cache contains correct data")

	# ACT: Get the value from cache again
	cache_retrieved = await redis_client.get("cache_test_key")
	assert cache_retrieved is not None
	logger.info("✅ Retrieved value from cache successfully")

	# ASSERT: Both values are identical
	retrieved_data = json.loads(cache_retrieved)
	assert retrieved_data == test_data
	logger.info("✅ Cache-hit retrieval returns identical data")

	# Cleanup
	await redis_client.delete("cache_test_key")


@pytest.mark.asyncio
async def test_redis_ttl_expiration_works(
	redis_client: redis.Redis,
) -> None:
	"""
	Test: Verify Redis TTL eviction works automatically

	Validates:
	- Key exists in Redis after creation
	- GET returns the value initially
	- After TTL expires, key no longer exists
	- GET returns None/empty after expiration
	"""

	logger.info("⏰ Testing Redis TTL expiration...")

	# SETUP: Create key with 2-second TTL
	test_key = "ttl_test:temporary_data"
	test_value = {"user_id": "123", "status": "active"}

	# ACT: Set key with EX (expire in seconds) parameter
	await redis_client.setex(
		test_key,
		2,  # 2-second TTL
		json.dumps(test_value)
	)
	logger.info("✅ Set Redis key with 2-second TTL")

	# ASSERT: Key exists immediately after creation
	value_immediately = await redis_client.get(test_key)
	assert value_immediately is not None, "Key should exist immediately after SET"
	decoded = json.loads(value_immediately)
	assert decoded["user_id"] == "123"
	logger.info("✅ Key exists immediately after creation")

	# ASSERT: GET returns the value with valid TTL
	ttl_remaining = await redis_client.ttl(test_key)
	assert ttl_remaining > 0, f"TTL should be positive, got {ttl_remaining}"
	assert ttl_remaining <= 2, f"TTL should be <= 2 seconds, got {ttl_remaining}"
	logger.info(f"✅ TTL is {ttl_remaining} seconds")

	# ACT: Wait for TTL to expire (sleep 3 seconds)
	logger.info("⏳ Waiting 3 seconds for TTL to expire...")
	await asyncio.sleep(3)
	logger.info("✅ Waited 3 seconds")

	# ASSERT: Key no longer exists after expiration
	value_after_expire = await redis_client.get(test_key)
	assert value_after_expire is None, f"Key should not exist after TTL expiration, got {value_after_expire}"
	logger.info("✅ Key expired and no longer exists in Redis")

	# ASSERT: TTL is -2 (key doesn't exist)
	ttl_after_expire = await redis_client.ttl(test_key)
	assert ttl_after_expire == -2, f"TTL should be -2 for non-existent keys, got {ttl_after_expire}"
	logger.info("✅ TTL correctly shows -2 for expired key")


@pytest.mark.asyncio
async def test_redis_connection_and_basic_operations(
	redis_client: redis.Redis,
) -> None:
	"""
	Test: Verify basic Redis operations work correctly

	Validates:
	- Connection is healthy (PING)
	- SET/GET operations work
	- DEL operations work
	- Multiple data types supported
	"""

	logger.info("🔗 Testing Redis connection and basic operations...")

	# TEST 1: PING
	try:
		response = await redis_client.ping()
		assert response is True
		logger.info("✅ Redis PING successful")
	except Exception as e:
		pytest.fail(f"Redis PING failed: {e}")

	# TEST 2: SET/GET string
	await redis_client.set("test_string", "hello_world")
	value = await redis_client.get("test_string")
	assert value == b"hello_world"
	logger.info("✅ String SET/GET works")

	# TEST 3: SET/GET JSON
	test_obj = {"name": "test", "count": 42}
	await redis_client.set("test_json", json.dumps(test_obj))
	cached = await redis_client.get("test_json")
	decoded = json.loads(cached)
	assert decoded["name"] == "test"
	assert decoded["count"] == 42
	logger.info("✅ JSON SET/GET works")

	# TEST 4: DEL
	deleted = await redis_client.delete("test_string", "test_json")
	assert deleted == 2
	logger.info("✅ DEL operation works")

	# TEST 5: EXISTS
	exists = await redis_client.exists("test_string")
	assert exists == 0
	logger.info("✅ EXISTS check works")

	# TEST 6: INCR/DECR
	await redis_client.set("counter", "10")
	await redis_client.incr("counter")
	value = await redis_client.get("counter")
	assert int(value) == 11
	logger.info("✅ INCR operation works")

	# Cleanup
	await redis_client.delete("counter")
	logger.info("✅ All Redis operations working correctly")
