"""Unit tests for main application setup."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


def test_app_creation():
	"""Test that FastAPI app is created with correct configuration."""
	with (
		patch("ai_ticket_platform.main.initialize_logger"),
		patch("ai_ticket_platform.main.settings.initialize_settings") as mock_settings,
		patch("ai_ticket_platform.main.clients.initialize_aws_s3_client"),
		patch("ai_ticket_platform.main.clients.initialize_redis_client") as mock_redis_init,
		patch("ai_ticket_platform.main.clients.initialize_chroma_vectorstore"),
	):
		# Mock settings
		mock_settings_obj = MagicMock()
		mock_settings.return_value = mock_settings_obj

		# Mock redis client
		mock_redis = MagicMock()
		mock_redis.get_client = AsyncMock(return_value=MagicMock())
		mock_redis_init.return_value = mock_redis

		from ai_ticket_platform.main import app

		assert app.title == "AI Ticket Platform"
		# Check app has router_lifespan (lifespan is internal to FastAPI)
		assert app.router is not None


def test_cors_middleware_configured():
	"""Test that CORS middleware is properly configured."""
	with (
		patch("ai_ticket_platform.main.initialize_logger"),
		patch("ai_ticket_platform.main.settings.initialize_settings"),
		patch("ai_ticket_platform.main.clients.initialize_aws_s3_client"),
		patch("ai_ticket_platform.main.clients.initialize_redis_client") as mock_redis_init,
		patch("ai_ticket_platform.main.clients.initialize_chroma_vectorstore"),
	):
		mock_redis = MagicMock()
		mock_redis.get_client = AsyncMock(return_value=MagicMock())
		mock_redis_init.return_value = mock_redis

		from ai_ticket_platform.main import app

		# Check middleware exists
		assert len(app.user_middleware) > 0, "No middleware configured"


def test_routers_registered():
	"""Test that all routers are registered with /api prefix."""
	with (
		patch("ai_ticket_platform.main.initialize_logger"),
		patch("ai_ticket_platform.main.settings.initialize_settings"),
		patch("ai_ticket_platform.main.clients.initialize_aws_s3_client"),
		patch("ai_ticket_platform.main.clients.initialize_redis_client") as mock_redis_init,
		patch("ai_ticket_platform.main.clients.initialize_chroma_vectorstore"),
	):
		mock_redis = MagicMock()
		mock_redis.get_client = AsyncMock(return_value=MagicMock())
		mock_redis_init.return_value = mock_redis

		from ai_ticket_platform.main import app

		# Check that routers are registered
		routes = [route.path for route in app.routes]

		# Verify key routes exist
		assert any("/api/health" in route for route in routes), "Health router not found"
		assert any(
			"/api/tickets" in route for route in routes
		), "Tickets router not found"
		assert any(
			"/api/slack" in route for route in routes
		), "Slack router not found"


def test_widget_static_files_mounted():
	"""Test that widget static files are mounted."""
	with (
		patch("ai_ticket_platform.main.initialize_logger"),
		patch("ai_ticket_platform.main.settings.initialize_settings"),
		patch("ai_ticket_platform.main.clients.initialize_aws_s3_client"),
		patch("ai_ticket_platform.main.clients.initialize_redis_client") as mock_redis_init,
		patch("ai_ticket_platform.main.clients.initialize_chroma_vectorstore"),
	):
		mock_redis = MagicMock()
		mock_redis.get_client = AsyncMock(return_value=MagicMock())
		mock_redis_init.return_value = mock_redis

		from ai_ticket_platform.main import app

		# Check that /widget is mounted
		routes = [route.path for route in app.routes]
		assert any("/widget" in route for route in routes), "Widget static files not mounted"


@pytest.mark.asyncio
async def test_lifespan_startup():
	"""Test lifespan startup initializations."""
	with (
		patch("ai_ticket_platform.main.initialize_logger") as mock_logger,
		patch("ai_ticket_platform.main.settings.initialize_settings") as mock_settings,
		patch("ai_ticket_platform.main.clients.initialize_aws_s3_client") as mock_s3,
		patch("ai_ticket_platform.main.clients.initialize_redis_client") as mock_redis_init,
		patch("ai_ticket_platform.main.clients.initialize_chroma_vectorstore") as mock_chroma,
	):
		# Mock settings
		mock_settings_obj = MagicMock()
		mock_settings.return_value = mock_settings_obj

		# Mock redis client
		mock_redis = MagicMock()
		mock_redis_instance = MagicMock()
		mock_redis.get_client = AsyncMock(return_value=mock_redis_instance)
		mock_redis_init.return_value = mock_redis

		# Mock S3 client
		mock_s3_client = MagicMock()
		mock_s3.return_value = mock_s3_client

		# Mock chroma
		mock_chroma_vs = MagicMock()
		mock_chroma.return_value = mock_chroma_vs

		from ai_ticket_platform.main import lifespan, FastAPI

		app = FastAPI()

		async with lifespan(app):
			# Verify all initialization methods were called
			mock_logger.assert_called_once()
			mock_settings.assert_called_once()
			mock_s3.assert_called_once()
			mock_redis_init.assert_called_once()
			mock_redis.get_client.assert_called_once()
			mock_chroma.assert_called_once_with(mock_settings_obj)


@pytest.mark.asyncio
async def test_lifespan_shutdown():
	"""Test lifespan shutdown logging."""
	with (
		patch("ai_ticket_platform.main.initialize_logger"),
		patch("ai_ticket_platform.main.settings.initialize_settings") as mock_settings,
		patch("ai_ticket_platform.main.clients.initialize_aws_s3_client"),
		patch("ai_ticket_platform.main.clients.initialize_redis_client") as mock_redis_init,
		patch("ai_ticket_platform.main.clients.initialize_chroma_vectorstore"),
		patch("ai_ticket_platform.main.logger.debug") as mock_debug,
	):
		# Mock settings
		mock_settings_obj = MagicMock()
		mock_settings.return_value = mock_settings_obj

		# Mock redis
		mock_redis = MagicMock()
		mock_redis.get_client = AsyncMock(return_value=MagicMock())
		mock_redis_init.return_value = mock_redis

		from ai_ticket_platform.main import lifespan, FastAPI

		app = FastAPI()

		async with lifespan(app):
			pass  # Enter and exit

		# Verify shutdown debug log was called
		mock_debug.assert_called_once_with("INFO:     Application shutdown complete.")
