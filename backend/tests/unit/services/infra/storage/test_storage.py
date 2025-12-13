"""Unit tests for storage service factory."""

import pytest
from unittest.mock import patch, MagicMock


class TestGetStorageService:
	"""Test get_storage_service factory function."""

	def test_get_storage_service_aws_success(self):
		"""Test that AWS storage service is returned when CLOUD_PROVIDER=aws."""
		from ai_ticket_platform.services.infra.storage.storage import (
			get_storage_service,
		)

		with patch.dict(
			"os.environ", {"CLOUD_PROVIDER": "aws", "S3_MAIN_BUCKET_NAME": "test-bucket"}
		):
			with patch(
				"ai_ticket_platform.services.infra.storage.aws.AWSS3Storage"
			) as mock_aws:
				mock_instance = MagicMock()
				mock_aws.return_value = mock_instance

				result = get_storage_service()

				assert result == mock_instance
				mock_aws.assert_called_once_with(bucket_name="test-bucket")

	def test_get_storage_service_aws_missing_bucket(self):
		"""Test that ValueError is raised when S3_MAIN_BUCKET_NAME is not set."""
		from ai_ticket_platform.services.infra.storage.storage import (
			get_storage_service,
		)

		with patch.dict("os.environ", {"CLOUD_PROVIDER": "aws"}, clear=True):
			with pytest.raises(ValueError) as exc_info:
				get_storage_service()

			assert "S3_MAIN_BUCKET_NAME not set" in str(exc_info.value)

	def test_get_storage_service_azure_success(self):
		"""Test that Azure storage service is returned when CLOUD_PROVIDER=azure."""
		from ai_ticket_platform.services.infra.storage.storage import (
			get_storage_service,
		)

		with patch.dict(
			"os.environ",
			{"CLOUD_PROVIDER": "azure", "AZURE_STORAGE_CONTAINER_NAME": "test-container"},
		):
			with patch(
				"ai_ticket_platform.services.infra.storage.azure.AzureBlobStorage"
			) as mock_azure:
				mock_instance = MagicMock()
				mock_azure.return_value = mock_instance

				result = get_storage_service()

				assert result == mock_instance
				mock_azure.assert_called_once_with(container_name="test-container")

	def test_get_storage_service_azure_missing_container(self):
		"""Test that ValueError is raised when AZURE_STORAGE_CONTAINER_NAME is not set."""
		from ai_ticket_platform.services.infra.storage.storage import (
			get_storage_service,
		)

		with patch.dict("os.environ", {"CLOUD_PROVIDER": "azure"}, clear=True):
			with pytest.raises(ValueError) as exc_info:
				get_storage_service()

			assert "AZURE_STORAGE_CONTAINER_NAME not set" in str(exc_info.value)

	def test_get_storage_service_defaults_to_aws(self):
		"""Test that AWS storage service is returned when CLOUD_PROVIDER is not set."""
		from ai_ticket_platform.services.infra.storage.storage import (
			get_storage_service,
		)

		with patch.dict("os.environ", {"S3_MAIN_BUCKET_NAME": "default-bucket"}):
			with patch.dict("os.environ", {}, clear=False):
				# Clear CLOUD_PROVIDER if it exists
				import os

				os.environ.pop("CLOUD_PROVIDER", None)

				with patch(
					"ai_ticket_platform.services.infra.storage.aws.AWSS3Storage"
				) as mock_aws:
					mock_instance = MagicMock()
					mock_aws.return_value = mock_instance

					result = get_storage_service()

					assert result == mock_instance
					mock_aws.assert_called_once_with(bucket_name="default-bucket")
