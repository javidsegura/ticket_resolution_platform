"""Redis cache manager with core caching logic and helpers."""

import json
import logging
from typing import Any, Awaitable, Callable, Optional

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class CacheManager:
	"""Async Redis cache manager with helper functions."""

	def __init__(self, redis_client: Redis) -> None:
		"""
		Create a CacheManager bound to the provided Redis client.
		
		Stores the Redis client on the instance for use by the cache operations.
		"""
		self.redis = redis_client

	async def get(self, key: str) -> Optional[dict[str, Any]]:
		"""
		Retrieve a JSON-decoded dictionary stored under the given cache key.
		
		Parameters:
		    key (str): Cache key to fetch.
		
		Returns:
		    dict[str, Any] or None: Parsed JSON value if the key exists, otherwise None.
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
			logger.warning(f"Cache get error for key {key}: {e}", exc_info=True)
			return None

	async def set(self, key: str, value: dict[str, Any], ttl: int) -> bool:
		"""
		Store a dictionary in the cache under the given key with the specified TTL.
		
		Parameters:
		    key (str): Cache key.
		    value (dict[str, Any]): Dictionary to store (will be serialized).
		    ttl (int): Time-to-live in seconds.
		
		Returns:
		    bool: `True` if the value was stored, `False` otherwise.
		"""
		if not self.redis:
			return False

		try:
			await self.redis.setex(key, ttl, json.dumps(value))
			return True
		except Exception as e:
			# Log error but don't fail - cache write failures shouldn't break app
			logger.warning(f"Cache set error for key {key}: {e}", exc_info=True)
			return False

	async def delete(self, key: str) -> bool:
		"""
		Deletes the value stored for the given cache key.
		
		Parameters:
		    key (str): Cache key to remove.
		
		Returns:
		    True if the key was deleted successfully, False otherwise.
		"""
		if not self.redis:
			return False

		try:
			await self.redis.delete(key)
			return True
		except Exception as e:
			# Log error but don't fail
			logger.warning(f"Cache delete error for key {key}: {e}", exc_info=True)
			return False

	async def get_or_fetch(
		self,
		key: str,
		fetch_fn: Callable[[], Awaitable[dict[str, Any]]],
		ttl: int,
	) -> dict[str, Any]:
		"""
		Retrieve a cached value for a key or fetch, cache, and return fresh data.
		
		Parameters:
		    key (str): Cache key.
		    fetch_fn (Callable[[], Awaitable[dict[str, Any]]]): Async function that returns the data to cache when there is a cache miss.
		    ttl (int): Time-to-live for the cached value in seconds.
		
		Returns:
		    dict[str, Any]: The cached or freshly fetched data for the given key.
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
		"""
		Invalidate the cache entry for the given key.
		
		Parameters:
		    key (str): Cache key to remove.
		
		Returns:
		    True if the key was successfully removed or the delete operation succeeded, False otherwise.
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
			logger.warning(f"Cache exists error for key {key}: {e}", exc_info=True)
			return False