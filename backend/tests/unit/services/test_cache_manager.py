"""Unit tests for cache manager service."""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from redis.asyncio import Redis

from ai_ticket_platform.services.caching.cache_manager import CacheManager


@pytest.mark.asyncio
class TestCacheManagerGet:
	"""Test CacheManager.get method."""

	async def test_get_success(self):
		"""Test successful cache get."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.get = AsyncMock(return_value=json.dumps({"key": "value"}))

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.get("test_key")

		assert result == {"key": "value"}
		mock_redis.get.assert_called_once_with("test_key")

	async def test_get_not_found(self):
		"""Test cache get when key doesn't exist."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.get = AsyncMock(return_value=None)

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.get("nonexistent_key")

		assert result is None

	async def test_get_no_redis(self):
		"""Test cache get when Redis is not available."""
		cache_manager = CacheManager(None)

		result = await cache_manager.get("test_key")

		assert result is None

	async def test_get_exception(self):
		"""Test cache get when Redis raises exception."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.get("test_key")

		assert result is None


@pytest.mark.asyncio
class TestCacheManagerSet:
	"""Test CacheManager.set method."""

	async def test_set_success(self):
		"""Test successful cache set."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.setex = AsyncMock()

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.set("test_key", {"data": "value"}, 300)

		assert result is True
		mock_redis.setex.assert_called_once_with("test_key", 300, json.dumps({"data": "value"}))

	async def test_set_no_redis(self):
		"""Test cache set when Redis is not available."""
		cache_manager = CacheManager(None)

		result = await cache_manager.set("test_key", {"data": "value"}, 300)

		assert result is False

	async def test_set_exception(self):
		"""Test cache set when Redis raises exception."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.set("test_key", {"data": "value"}, 300)

		assert result is False


@pytest.mark.asyncio
class TestCacheManagerDelete:
	"""Test CacheManager.delete method."""

	async def test_delete_success(self):
		"""Test successful cache delete."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.delete = AsyncMock()

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.delete("test_key")

		assert result is True
		mock_redis.delete.assert_called_once_with("test_key")

	async def test_delete_no_redis(self):
		"""Test cache delete when Redis is not available."""
		cache_manager = CacheManager(None)

		result = await cache_manager.delete("test_key")

		assert result is False

	async def test_delete_exception(self):
		"""Test cache delete when Redis raises exception."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.delete("test_key")

		assert result is False


@pytest.mark.asyncio
class TestCacheManagerGetOrFetch:
	"""Test CacheManager.get_or_fetch method."""

	async def test_get_or_fetch_cache_hit(self):
		"""Test get_or_fetch with cache hit."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.get = AsyncMock(return_value=json.dumps({"cached": "data"}))

		cache_manager = CacheManager(mock_redis)

		fetch_fn = AsyncMock(return_value={"fresh": "data"})

		result = await cache_manager.get_or_fetch("test_key", fetch_fn, 300)

		assert result == {"cached": "data"}
		fetch_fn.assert_not_called()

	async def test_get_or_fetch_cache_miss(self):
		"""Test get_or_fetch with cache miss."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.get = AsyncMock(return_value=None)
		mock_redis.setex = AsyncMock()

		cache_manager = CacheManager(mock_redis)

		fetch_fn = AsyncMock(return_value={"fresh": "data"})

		result = await cache_manager.get_or_fetch("test_key", fetch_fn, 300)

		assert result == {"fresh": "data"}
		fetch_fn.assert_called_once()
		mock_redis.setex.assert_called_once()

	async def test_get_or_fetch_fetch_exception(self):
		"""Test get_or_fetch when fetch function raises exception."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.get = AsyncMock(return_value=None)

		cache_manager = CacheManager(mock_redis)

		fetch_fn = AsyncMock(side_effect=Exception("Fetch error"))

		with pytest.raises(Exception, match="Fetch error"):
			await cache_manager.get_or_fetch("test_key", fetch_fn, 300)


@pytest.mark.asyncio
class TestCacheManagerInvalidate:
	"""Test CacheManager.invalidate method."""

	async def test_invalidate_success(self):
		"""Test successful cache invalidation."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.delete = AsyncMock()

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.invalidate("test_key")

		assert result is True
		mock_redis.delete.assert_called_once_with("test_key")

	async def test_invalidate_no_redis(self):
		"""Test cache invalidation when Redis is not available."""
		cache_manager = CacheManager(None)

		result = await cache_manager.invalidate("test_key")

		assert result is False


@pytest.mark.asyncio
class TestCacheManagerExists:
	"""Test CacheManager.exists method."""

	async def test_exists_true(self):
		"""Test exists when key is present."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.exists = AsyncMock(return_value=1)

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.exists("test_key")

		assert result is True
		mock_redis.exists.assert_called_once_with("test_key")

	async def test_exists_false(self):
		"""Test exists when key is not present."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.exists = AsyncMock(return_value=0)

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.exists("test_key")

		assert result is False

	async def test_exists_no_redis(self):
		"""Test exists when Redis is not available."""
		cache_manager = CacheManager(None)

		result = await cache_manager.exists("test_key")

		assert result is False

	async def test_exists_exception(self):
		"""Test exists when Redis raises exception."""
		mock_redis = MagicMock(spec=Redis)
		mock_redis.exists = AsyncMock(side_effect=Exception("Redis error"))

		cache_manager = CacheManager(mock_redis)

		result = await cache_manager.exists("test_key")

		assert result is False
