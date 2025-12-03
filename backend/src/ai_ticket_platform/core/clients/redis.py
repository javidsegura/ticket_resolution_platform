import redis.asyncio as r
import redis as sync_redis
from redis.client import Redis

from ai_ticket_platform.core.settings import initialize_settings

import logging

logger = logging.getLogger(__name__)


class RedisClientConnector:
	def __init__(self) -> None:
		self._client = None
		self.app_settings = initialize_settings()

	async def connect(self) -> Redis:
		if not self._client:
			self._client = r.from_url(
				url=self.app_settings.REDIS_URL,
				encoding="utf-8",
				decode_responses=True,
				max_connections=1,
			)
		logger.debug(f"REDIS CLIENT ID: {id(self._client)}")
		return self._client

	async def get_client(self) -> Redis:
		if not self._client:
			logger.debug(f"CLIENT DIDNT EXIST BEFORE!")
			return await self.connect()
		logger.debug(f"REDIS CLIENT ID: {id(self._client)}")
		return self._client

	async def close(self) -> None:
		if self._client:
			logger.debug(f"REDIS CLIENT ID: {id(self._client)}")
			await self._client.aclose()
			self._client = None

	def get_sync_connection(self) -> sync_redis.Redis:
		"""
		Get a synchronous Redis connection for libraries that require it (e.g., RQ).
		RQ and other synchronous libraries cannot use async Redis clients.
		"""
		return sync_redis.from_url(
			url=self.app_settings.REDIS_URL,
			decode_responses=False,
		)


redis_client = None


def initialize_redis_client():
	global redis_client
	if not redis_client:
		redis_client = RedisClientConnector()
	return redis_client
