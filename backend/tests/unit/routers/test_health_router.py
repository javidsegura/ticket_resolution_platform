"""Unit tests for health router endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ai_ticket_platform.routers.health import router


@pytest.mark.asyncio
class TestHealthPing:
	"""Test /health/ping endpoint."""

	async def test_ping_endpoint_success(self):
		"""Test ping endpoint returns pong."""
		# Health router has 2 routes: dependencies (index 0) and ping (index 1)
		ping_endpoint = router.routes[1].endpoint

		result = await ping_endpoint()

		assert result == {"response": "pong"}


@pytest.mark.asyncio
class TestHealthDependencies:
	"""Test /health/dependencies endpoint."""

	async def test_dependencies_all_healthy(self):
		"""Test dependencies endpoint when all services are healthy."""
		# Mock dependencies
		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()
		mock_redis = MagicMock()

		# Mock workers list
		mock_worker_1 = MagicMock()
		mock_worker_2 = MagicMock()

		# Health router has 2 routes: dependencies (index 0) and ping (index 1)
		deps_endpoint = router.routes[0].endpoint

		with patch("ai_ticket_platform.routers.health.test_redis_connection", new=AsyncMock(return_value=True)):
			with patch("ai_ticket_platform.routers.health.Worker.all", return_value=[mock_worker_1, mock_worker_2]):
				result = await deps_endpoint(
					db=mock_db,
					settings=mock_settings,
					sync_redis_connection=mock_redis
				)

				assert result["status"] == "healthy"
				assert result["checks"]["redis"] == "ok"
				assert "2 active" in result["checks"]["workers"]

	async def test_dependencies_redis_unhealthy(self):
		"""Test dependencies endpoint when Redis is unhealthy."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()
		mock_redis = MagicMock()
		mock_worker = MagicMock()

		deps_endpoint = router.routes[0].endpoint

		# Mock with workers present so status stays "unhealthy"
		with patch("ai_ticket_platform.routers.health.test_redis_connection", new=AsyncMock(return_value=False)):
			with patch("ai_ticket_platform.routers.health.Worker.all", return_value=[mock_worker]):
				with pytest.raises(HTTPException) as exc_info:
					await deps_endpoint(
						db=mock_db,
						settings=mock_settings,
						sync_redis_connection=mock_redis
					)

				assert exc_info.value.status_code == 503
				assert "unhealthy" in str(exc_info.value.detail)

	async def test_dependencies_redis_exception(self):
		"""Test dependencies endpoint when Redis raises exception."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()
		mock_redis = MagicMock()
		mock_worker = MagicMock()

		deps_endpoint = router.routes[0].endpoint

		# Mock with workers present so status stays "unhealthy"
		with patch("ai_ticket_platform.routers.health.test_redis_connection", new=AsyncMock(side_effect=ConnectionError("Redis down"))):
			with patch("ai_ticket_platform.routers.health.Worker.all", return_value=[mock_worker]):
				with pytest.raises(HTTPException) as exc_info:
					await deps_endpoint(
						db=mock_db,
						settings=mock_settings,
						sync_redis_connection=mock_redis
					)

				assert exc_info.value.status_code == 503

	async def test_dependencies_no_workers_degraded(self):
		"""Test dependencies endpoint when no workers are active (degraded state)."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()
		mock_redis = MagicMock()

		deps_endpoint = router.routes[0].endpoint

		with patch("ai_ticket_platform.routers.health.test_redis_connection", new=AsyncMock(return_value=True)):
			with patch("ai_ticket_platform.routers.health.Worker.all", return_value=[]):
				result = await deps_endpoint(
					db=mock_db,
					settings=mock_settings,
					sync_redis_connection=mock_redis
				)

				assert result["status"] == "degraded"
				assert result["checks"]["redis"] == "ok"
				assert "0 active" in result["checks"]["workers"]

	async def test_dependencies_worker_exception(self):
		"""Test dependencies endpoint when Worker.all raises exception."""
		mock_db = MagicMock(spec=AsyncSession)
		mock_settings = MagicMock()
		mock_redis = MagicMock()

		deps_endpoint = router.routes[0].endpoint

		with patch("ai_ticket_platform.routers.health.test_redis_connection", new=AsyncMock(return_value=True)):
			with patch("ai_ticket_platform.routers.health.Worker.all", side_effect=Exception("Worker error")):
				with pytest.raises(HTTPException) as exc_info:
					await deps_endpoint(
						db=mock_db,
						settings=mock_settings,
						sync_redis_connection=mock_redis
					)

				assert exc_info.value.status_code == 503
				assert "unhealthy" in str(exc_info.value.detail)
