"""Unit tests for database engine initialization."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


class TestInitializeDbEngine:
	"""Test initialize_db_engine function."""

	def test_initialize_db_engine_first_call(self):
		"""Test first initialization creates engine and session maker."""
		from ai_ticket_platform.database import main

		# Reset global state
		main.AsyncSessionLocal = None

		mock_settings = MagicMock()
		mock_settings.MYSQL_ASYNC_DRIVER = "mysql+aiomysql"
		mock_settings.MYSQL_USER = "test_user"
		mock_settings.MYSQL_PASSWORD = "test_password"
		mock_settings.MYSQL_HOST = "localhost"
		mock_settings.MYSQL_PORT = "3306"
		mock_settings.MYSQL_DATABASE = "test_db"

		mock_engine = MagicMock()
		mock_session_maker = MagicMock()

		with patch(
			"ai_ticket_platform.database.main.initialize_settings",
			return_value=mock_settings,
		):
			with patch("ai_ticket_platform.database.main.os.getenv", return_value="production"):
				with patch(
					"ai_ticket_platform.database.main.create_async_engine",
					return_value=mock_engine,
				) as mock_create_engine:
					with patch(
						"ai_ticket_platform.database.main.async_sessionmaker",
						return_value=mock_session_maker,
					) as mock_sessionmaker:
						result = main.initialize_db_engine()

						assert result == mock_session_maker
						assert main.AsyncSessionLocal == mock_session_maker

						# Verify engine was created with correct URL
						call_args = mock_create_engine.call_args
						assert (
							"mysql+aiomysql://test_user:test_password@localhost:3306/test_db"
							in call_args[0]
						)

						# Verify engine configuration (production mode with pooling)
						assert call_args[1]["echo"] is False
						assert call_args[1]["pool_size"] == 10
						assert call_args[1]["max_overflow"] == 20
						assert call_args[1]["pool_pre_ping"] is True
						assert call_args[1]["pool_recycle"] == 3600

						# Verify session maker was created
						mock_sessionmaker.assert_called_once()

	def test_initialize_db_engine_already_initialized(self):
		"""Test that subsequent calls return existing session maker."""
		from ai_ticket_platform.database import main

		# Set up existing session maker
		existing_session_maker = MagicMock()
		main.AsyncSessionLocal = existing_session_maker

		with patch(
			"ai_ticket_platform.database.main.initialize_settings"
		) as mock_init_settings:
			with patch(
				"ai_ticket_platform.database.main.create_async_engine"
			) as mock_create_engine:
				result = main.initialize_db_engine()

				assert result == existing_session_maker
				# Settings should still be called
				mock_init_settings.assert_called_once()
				# But engine should NOT be created again
				mock_create_engine.assert_not_called()

	def test_initialize_db_engine_database_url_construction(self):
		"""Test that database URL is constructed correctly with different values."""
		from ai_ticket_platform.database import main

		main.AsyncSessionLocal = None

		mock_settings = MagicMock()
		mock_settings.MYSQL_ASYNC_DRIVER = "mysql+asyncmy"
		mock_settings.MYSQL_USER = "admin"
		mock_settings.MYSQL_PASSWORD = "secret123"
		mock_settings.MYSQL_HOST = "db.example.com"
		mock_settings.MYSQL_PORT = "3307"
		mock_settings.MYSQL_DATABASE = "production_db"

		with patch(
			"ai_ticket_platform.database.main.initialize_settings",
			return_value=mock_settings,
		):
			with patch("ai_ticket_platform.database.main.os.getenv", return_value="dev"):
				with patch(
					"ai_ticket_platform.database.main.create_async_engine"
				) as mock_create_engine:
					with patch("ai_ticket_platform.database.main.async_sessionmaker"):
						main.initialize_db_engine()

						call_args = mock_create_engine.call_args
						expected_url = (
							"mysql+asyncmy://admin:secret123@db.example.com:3307/production_db"
						)
						assert expected_url in call_args[0]

	def test_initialize_db_engine_test_environment_uses_nullpool(self):
		"""Test that test environment uses NullPool to avoid event loop issues."""
		from ai_ticket_platform.database import main

		main.AsyncSessionLocal = None

		mock_settings = MagicMock()
		mock_settings.MYSQL_ASYNC_DRIVER = "mysql+aiomysql"
		mock_settings.MYSQL_USER = "test_user"
		mock_settings.MYSQL_PASSWORD = "test_password"
		mock_settings.MYSQL_HOST = "localhost"
		mock_settings.MYSQL_PORT = "3306"
		mock_settings.MYSQL_DATABASE = "test_db"

		mock_engine = MagicMock()
		mock_session_maker = MagicMock()

		with patch(
			"ai_ticket_platform.database.main.initialize_settings",
			return_value=mock_settings,
		):
			with patch("ai_ticket_platform.database.main.os.getenv", return_value="test"):
				with patch(
					"ai_ticket_platform.database.main.create_async_engine",
					return_value=mock_engine,
				) as mock_create_engine:
					with patch(
						"ai_ticket_platform.database.main.async_sessionmaker",
						return_value=mock_session_maker,
					):
						result = main.initialize_db_engine()

						assert result == mock_session_maker

						# Verify engine configuration (test mode with NullPool)
						call_args = mock_create_engine.call_args
						assert call_args[1]["echo"] is False
						assert "poolclass" in call_args[1]
						# No pool_size, max_overflow, etc. in test mode
