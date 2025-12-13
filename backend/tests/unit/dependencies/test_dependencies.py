"""Unit tests for dependency injection functions."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestGetDb:
	"""Test get_db database session dependency."""

	async def test_get_db_yields_session(self):
		"""Test that get_db yields an async database session."""
		from ai_ticket_platform.dependencies.database import get_db

		mock_session = MagicMock(spec=AsyncSession)
		mock_session.close = AsyncMock()
		mock_session_local = MagicMock()
		mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
		mock_session_local.return_value.__aexit__ = AsyncMock()

		with patch(
			"ai_ticket_platform.dependencies.database.initialize_db_engine",
			return_value=mock_session_local,
		):
			generator = get_db()
			session = await generator.__anext__()

			assert session == mock_session

			# Cleanup
			try:
				await generator.__anext__()
			except StopAsyncIteration:
				pass

	async def test_get_db_closes_session_on_exit(self):
		"""Test that session is closed when generator exits."""
		from ai_ticket_platform.dependencies.database import get_db

		mock_session = MagicMock(spec=AsyncSession)
		mock_session.close = AsyncMock()
		mock_session_local = MagicMock()
		mock_session_local.return_value.__aenter__ = AsyncMock(return_value=mock_session)
		mock_session_local.return_value.__aexit__ = AsyncMock()

		with patch(
			"ai_ticket_platform.dependencies.database.initialize_db_engine",
			return_value=mock_session_local,
		):
			generator = get_db()
			await generator.__anext__()

			# Trigger cleanup
			try:
				await generator.__anext__()
			except StopAsyncIteration:
				pass

			mock_session.close.assert_called_once()


@pytest.mark.asyncio
class TestGetAppSettings:
	"""Test get_app_settings dependency."""

	async def test_get_app_settings_returns_dict(self):
		"""Test that get_app_settings returns settings dictionary."""
		from ai_ticket_platform.dependencies.settings import get_app_settings

		mock_settings = {
			"ENVIRONMENT": "test",
			"MYSQL_HOST": "localhost",
			"REDIS_URL": "redis://localhost:6379",
		}

		with patch(
			"ai_ticket_platform.dependencies.settings.initialize_settings",
			return_value=mock_settings,
		):
			result = await get_app_settings()

			assert result == mock_settings
			assert isinstance(result, dict)
			assert "ENVIRONMENT" in result

	async def test_get_app_settings_calls_initialize(self):
		"""Test that get_app_settings calls initialize_settings."""
		from ai_ticket_platform.dependencies.settings import get_app_settings

		mock_settings = {"test": "value"}

		with patch(
			"ai_ticket_platform.dependencies.settings.initialize_settings",
			return_value=mock_settings,
		) as mock_init:
			await get_app_settings()

			mock_init.assert_called_once()


class TestGetQueue:
	"""Test get_queue dependency."""

	def test_get_queue_returns_queue_object(self):
		"""Test that get_queue returns RQ Queue object."""
		from ai_ticket_platform.dependencies.queue import get_queue

		mock_redis = MagicMock()
		mock_connector = MagicMock()
		mock_connector.get_sync_connection = MagicMock(return_value=mock_redis)

		with patch(
			"ai_ticket_platform.dependencies.queue.initialize_redis_client",
			return_value=mock_connector,
		):
			with patch("ai_ticket_platform.dependencies.queue.Queue") as mock_queue_class:
				mock_queue = MagicMock()
				mock_queue_class.return_value = mock_queue

				result = get_queue()

				assert result == mock_queue
				mock_queue_class.assert_called_once_with("default", connection=mock_redis)

	def test_get_sync_redis_connection(self):
		"""Test get_sync_redis_connection returns sync connection."""
		from ai_ticket_platform.dependencies.queue import get_sync_redis_connection

		mock_redis = MagicMock()
		mock_connector = MagicMock()
		mock_connector.get_sync_connection = MagicMock(return_value=mock_redis)

		with patch(
			"ai_ticket_platform.dependencies.queue.initialize_redis_client",
			return_value=mock_connector,
		):
			result = get_sync_redis_connection()

			assert result == mock_redis
			mock_connector.get_sync_connection.assert_called_once()
