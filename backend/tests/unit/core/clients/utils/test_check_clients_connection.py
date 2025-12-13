"""Unit tests for client connection checking utilities."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


class TestRedisConnection:
	"""Test Redis connection checking."""

	@pytest.mark.asyncio
	async def test_redis_connection_success(self):
		"""Test successful Redis connection check."""
		from ai_ticket_platform.core.clients.utils.check_clients_connection import (
			test_redis_connection,
		)

		with patch(
			"ai_ticket_platform.core.clients.utils.check_clients_connection.initialize_redis_client"
		) as mock_init:
			mock_connector = MagicMock()
			mock_client = AsyncMock()
			mock_client.ping.return_value = True

			mock_connector.get_client = AsyncMock(return_value=mock_client)
			mock_init.return_value = mock_connector

			result = await test_redis_connection()

			assert result is True
			mock_connector.get_client.assert_called_once()
			mock_client.ping.assert_called_once()

	@pytest.mark.asyncio
	async def test_redis_connection_ping_false(self):
		"""Test Redis connection check when ping returns False."""
		from ai_ticket_platform.core.clients.utils.check_clients_connection import (
			test_redis_connection,
		)

		with patch(
			"ai_ticket_platform.core.clients.utils.check_clients_connection.initialize_redis_client"
		) as mock_init:
			mock_connector = MagicMock()
			mock_client = AsyncMock()
			mock_client.ping.return_value = False

			mock_connector.get_client = AsyncMock(return_value=mock_client)
			mock_init.return_value = mock_connector

			result = await test_redis_connection()

			assert result is False


class TestDatabaseConnection:
	"""Test database connection checking."""

	@pytest.mark.asyncio
	async def test_db_connection_success(self):
		"""Test successful database connection check."""
		from ai_ticket_platform.core.clients.utils.check_clients_connection import (
			test_db_connection,
		)

		mock_db = AsyncMock(spec=AsyncSession)
		mock_db.execute = AsyncMock(return_value=None)

		result = await test_db_connection(db=mock_db)

		assert result is True
		mock_db.execute.assert_called_once()

	@pytest.mark.asyncio
	async def test_db_connection_failure(self):
		"""Test database connection check when query fails."""
		from ai_ticket_platform.core.clients.utils.check_clients_connection import (
			test_db_connection,
		)

		mock_db = AsyncMock(spec=AsyncSession)
		mock_db.execute = AsyncMock(side_effect=Exception("Connection failed"))

		result = await test_db_connection(db=mock_db)

		assert result is False
