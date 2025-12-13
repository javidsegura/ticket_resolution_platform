"""Unit tests for storage dependency."""

from unittest.mock import patch, MagicMock


class TestGetStorageServiceDependency:
	"""Test get_storage_service_dependency function."""

	def test_get_storage_service_dependency_returns_storage_service(self):
		"""Test that dependency returns storage service from factory."""
		from ai_ticket_platform.dependencies.storage import (
			get_storage_service_dependency,
		)

		with patch(
			"ai_ticket_platform.dependencies.storage.get_storage_service"
		) as mock_get_storage:
			mock_storage = MagicMock()
			mock_get_storage.return_value = mock_storage

			result = get_storage_service_dependency()

			assert result == mock_storage
			mock_get_storage.assert_called_once()
