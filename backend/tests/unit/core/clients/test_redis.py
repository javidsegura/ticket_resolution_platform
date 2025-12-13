"""Unit tests for Redis client."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestRedisClientConnector:
	"""Test RedisClientConnector class."""

	def test_redis_client_connector_init(self):
		"""Test RedisClientConnector initialization."""
		from ai_ticket_platform.core.clients.redis import RedisClientConnector

		with patch("ai_ticket_platform.core.clients.redis.initialize_settings") as mock_settings:
			mock_app_settings = MagicMock()
			mock_app_settings.REDIS_URL = "redis://localhost:6379"
			mock_settings.return_value = mock_app_settings

			connector = RedisClientConnector()

			assert connector._client is None
			assert connector.app_settings == mock_app_settings

	@pytest.mark.asyncio
	async def test_connect_creates_new_client(self):
		"""Test that connect creates a new Redis client."""
		from ai_ticket_platform.core.clients.redis import RedisClientConnector

		with patch("ai_ticket_platform.core.clients.redis.initialize_settings") as mock_settings:
			mock_app_settings = MagicMock()
			mock_app_settings.REDIS_URL = "redis://localhost:6379"
			mock_settings.return_value = mock_app_settings

			with patch("ai_ticket_platform.core.clients.redis.r.from_url") as mock_from_url:
				mock_redis_client = MagicMock()
				mock_from_url.return_value = mock_redis_client

				connector = RedisClientConnector()
				result = await connector.connect()

				assert result == mock_redis_client
				assert connector._client == mock_redis_client
				mock_from_url.assert_called_once_with(
					url="redis://localhost:6379",
					encoding="utf-8",
					decode_responses=True,
					max_connections=1,
				)

	@pytest.mark.asyncio
	async def test_get_client_creates_if_not_exists(self):
		"""Test that get_client creates client if it doesn't exist."""
		from ai_ticket_platform.core.clients.redis import RedisClientConnector

		with patch("ai_ticket_platform.core.clients.redis.initialize_settings") as mock_settings:
			mock_app_settings = MagicMock()
			mock_app_settings.REDIS_URL = "redis://localhost:6379"
			mock_settings.return_value = mock_app_settings

			with patch("ai_ticket_platform.core.clients.redis.r.from_url") as mock_from_url:
				mock_redis_client = MagicMock()
				mock_from_url.return_value = mock_redis_client

				connector = RedisClientConnector()
				result = await connector.get_client()

				assert result == mock_redis_client
				assert connector._client == mock_redis_client

	@pytest.mark.asyncio
	async def test_get_client_returns_existing(self):
		"""Test that get_client returns existing client."""
		from ai_ticket_platform.core.clients.redis import RedisClientConnector

		with patch("ai_ticket_platform.core.clients.redis.initialize_settings") as mock_settings:
			mock_app_settings = MagicMock()
			mock_app_settings.REDIS_URL = "redis://localhost:6379"
			mock_settings.return_value = mock_app_settings

			connector = RedisClientConnector()
			mock_existing_client = MagicMock()
			connector._client = mock_existing_client

			result = await connector.get_client()

			assert result == mock_existing_client

	@pytest.mark.asyncio
	async def test_close_closes_client(self):
		"""Test that close properly closes the Redis client."""
		from ai_ticket_platform.core.clients.redis import RedisClientConnector

		with patch("ai_ticket_platform.core.clients.redis.initialize_settings") as mock_settings:
			mock_app_settings = MagicMock()
			mock_app_settings.REDIS_URL = "redis://localhost:6379"
			mock_settings.return_value = mock_app_settings

			connector = RedisClientConnector()
			mock_client = AsyncMock()
			connector._client = mock_client

			await connector.close()

			mock_client.aclose.assert_called_once()
			assert connector._client is None

	@pytest.mark.asyncio
	async def test_close_does_nothing_if_no_client(self):
		"""Test that close does nothing if no client exists."""
		from ai_ticket_platform.core.clients.redis import RedisClientConnector

		with patch("ai_ticket_platform.core.clients.redis.initialize_settings") as mock_settings:
			mock_app_settings = MagicMock()
			mock_settings.return_value = mock_app_settings

			connector = RedisClientConnector()
			# No client set, should not raise error
			await connector.close()

			assert connector._client is None

	def test_get_sync_connection(self):
		"""Test getting synchronous Redis connection."""
		from ai_ticket_platform.core.clients.redis import RedisClientConnector

		with patch("ai_ticket_platform.core.clients.redis.initialize_settings") as mock_settings:
			mock_app_settings = MagicMock()
			mock_app_settings.REDIS_URL = "redis://localhost:6379"
			mock_settings.return_value = mock_app_settings

			with patch("ai_ticket_platform.core.clients.redis.sync_redis.from_url") as mock_from_url:
				mock_sync_client = MagicMock()
				mock_from_url.return_value = mock_sync_client

				connector = RedisClientConnector()
				result = connector.get_sync_connection()

				assert result == mock_sync_client
				mock_from_url.assert_called_once_with(
					url="redis://localhost:6379",
					decode_responses=False,
				)


class TestInitializeRedisClient:
	"""Test initialize_redis_client function."""

	def test_initialize_redis_client_first_time(self):
		"""Test initializing Redis client for the first time."""
		from ai_ticket_platform.core.clients.redis import initialize_redis_client
		import ai_ticket_platform.core.clients.redis as redis_module

		# Reset global
		redis_module.redis_client = None

		with patch("ai_ticket_platform.core.clients.redis.initialize_settings"):
			result = initialize_redis_client()

			assert result is not None
			assert redis_module.redis_client == result

	def test_initialize_redis_client_returns_existing(self):
		"""Test that existing Redis client is returned."""
		from ai_ticket_platform.core.clients.redis import initialize_redis_client
		import ai_ticket_platform.core.clients.redis as redis_module

		mock_existing = MagicMock()
		redis_module.redis_client = mock_existing

		result = initialize_redis_client()

		assert result == mock_existing
