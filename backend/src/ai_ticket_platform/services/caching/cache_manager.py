"""Redis cache manager with core caching logic and helpers."""

import json
from typing import Any, Awaitable, Callable, Optional

from redis.asyncio import Redis


class CacheManager:
	"""Async Redis cache manager with helper functions."""

	def __init__(self, redis_client: Redis) -> None:
		"""Initialize cache manager with Redis client.

		Args:
			redis_client: Async Redis client instance.
		"""
		self.redis = redis_client

	async def get(self, key: str) -> Optional[dict[str, Any]]:
		"""Get value from cache.

		Args:
			key: Cache key.

		Returns:
			Parsed JSON value if found, None otherwise.
		"""
		if not self.redis:
			return None

		try:
			value = await self.redis.get(key)
			if value is None:
				return None
			return json.loads(value)
		except Exception as e:
			# Log error but don't fail - cache misses should be recoverable
			print(f"Cache get error for key {key}: {e}")
			return None

	async def set(self, key: str, value: dict[str, Any], ttl: int) -> bool:
		"""Set value in cache with TTL.

		Args:
			key: Cache key.
			value: Dictionary value to cache.
			ttl: Time-to-live in seconds.

		Returns:
			True if successful, False otherwise.
		"""
		if not self.redis:
			return False

		try:
			await self.redis.setex(key, ttl, json.dumps(value))
			return True
		except Exception as e:
			# Log error but don't fail - cache write failures shouldn't break app
			print(f"Cache set error for key {key}: {e}")
			return False

	async def delete(self, key: str) -> bool:
		"""Delete value from cache.

		Args:
			key: Cache key.

		Returns:
			True if successful, False otherwise.
		"""
		if not self.redis:
			return False

		try:
			await self.redis.delete(key)
			return True
		except Exception as e:
			# Log error but don't fail
			print(f"Cache delete error for key {key}: {e}")
			return False

	async def get_or_fetch(
		self,
		key: str,
		fetch_fn: Callable[[], Awaitable[dict[str, Any]]],
		ttl: int,
	) -> dict[str, Any]:
		"""Get from cache or fetch and cache result.

		This is the primary helper for cache-aside pattern:
		1. Try to get from cache
		2. If miss, call fetch_fn to get data
		3. Cache the result
		4. Return data

		Args:
			key: Cache key.
			fetch_fn: Async function that returns data to cache.
			ttl: Time-to-live in seconds.

		Returns:
			Cached or freshly fetched data.

		Raises:
			Exception: If fetch_fn raises an exception.
		"""
		# Try cache first
		cached = await self.get(key)
		if cached is not None:
			return cached

		# Cache miss - fetch fresh data
		data = await fetch_fn()

		# Store in cache (don't fail if cache write fails)
		await self.set(key, data, ttl)

		return data

	async def invalidate(self, key: str) -> bool:
		"""Invalidate cache entry.

		Args:
			key: Cache key.

		Returns:
			True if successful, False otherwise.
		"""
		return await self.delete(key)

	async def exists(self, key: str) -> bool:
		"""Check if key exists in cache.

		Args:
			key: Cache key.

		Returns:
			True if key exists, False otherwise.
		"""
		if not self.redis:
			return False

		try:
			return await self.redis.exists(key) > 0
		except Exception as e:
			print(f"Cache exists error for key {key}: {e}")
			return False
