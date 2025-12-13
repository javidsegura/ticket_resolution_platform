"""Unit tests for storage service factory."""

import pytest
import os
from unittest.mock import patch, MagicMock


class TestGetStorageService:
	"""Test storage service factory function."""

	def test_get_storage_service_aws_default(self):
		"""Test factory returns AWS S3 storage by default."""
		env_vars = {
			"S3_MAIN_BUCKET_NAME": "test-bucket",
			"CLOUD_PROVIDER": "aws",
		}
		with (
			patch.dict(os.environ, env_vars, clear=False),
			patch(
				"ai_ticket_platform.services.infra.storage.aws.AWSS3Storage"
			) as mock_aws,
		):
			from ai_ticket_platform.services.infra.storage.storage import (
				get_storage_service,
			)

			mock_storage = MagicMock()
			mock_aws.return_value = mock_storage

			result = get_storage_service()

			assert result == mock_storage
			mock_aws.assert_called_once_with(bucket_name="test-bucket")

	def test_get_storage_service_aws_missing_bucket(self):
		"""Test factory raises error when S3 bucket name not set."""
		with patch.dict(os.environ, {"CLOUD_PROVIDER": "aws"}, clear=True):
			from ai_ticket_platform.services.infra.storage.storage import (
				get_storage_service,
			)

			with pytest.raises(ValueError, match="S3_MAIN_BUCKET_NAME not set"):
				get_storage_service()

	def test_get_storage_service_azure_missing_container(self):
		"""Test factory raises error when Azure container name not set."""
		with patch.dict(os.environ, {"CLOUD_PROVIDER": "azure"}, clear=True):
			from ai_ticket_platform.services.infra.storage.storage import (
				get_storage_service,
			)

			with pytest.raises(ValueError, match="AZURE_STORAGE_CONTAINER_NAME not set"):
				get_storage_service()
