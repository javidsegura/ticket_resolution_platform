"""Unit tests for Azure Blob Storage client initialization."""

import pytest
from unittest.mock import patch, MagicMock


class TestInitializeAzureBlobServiceClient:
	"""Test initialize_azure_blob_service_client function."""

	def test_initialize_azure_blob_service_client_success(self):
		"""Test successful Azure Blob Storage client initialization."""
		from ai_ticket_platform.core.clients.azure import (
			initialize_azure_blob_service_client,
		)

		with patch.dict(
			"os.environ",
			{
				"AZURE_STORAGE_ACCOUNT_NAME": "testaccount",
				"AZURE_STORAGE_ACCOUNT_KEY": "testkey123",
			},
		):
			with patch(
				"ai_ticket_platform.core.clients.azure.BlobServiceClient"
			) as mock_client:
				mock_instance = MagicMock()
				mock_client.return_value = mock_instance

				# Reset global client to None
				import ai_ticket_platform.core.clients.azure as azure_module

				azure_module.blob_service_client = None

				result = initialize_azure_blob_service_client()

				assert result == mock_instance
				mock_client.assert_called_once_with(
					account_url="https://testaccount.blob.core.windows.net",
					credential="testkey123",
				)

	def test_initialize_azure_blob_service_client_returns_existing(self):
		"""Test that existing client is returned without re-initialization."""
		from ai_ticket_platform.core.clients.azure import (
			initialize_azure_blob_service_client,
		)

		with patch.dict(
			"os.environ",
			{
				"AZURE_STORAGE_ACCOUNT_NAME": "testaccount",
				"AZURE_STORAGE_ACCOUNT_KEY": "testkey123",
			},
		):
			with patch(
				"ai_ticket_platform.core.clients.azure.BlobServiceClient"
			) as mock_client:
				mock_instance = MagicMock()
				mock_client.return_value = mock_instance

				# Set global client
				import ai_ticket_platform.core.clients.azure as azure_module

				azure_module.blob_service_client = mock_instance

				result = initialize_azure_blob_service_client()

				# Should return existing client without calling BlobServiceClient again
				assert result == mock_instance
				mock_client.assert_not_called()

				# Reset for other tests
				azure_module.blob_service_client = None

	def test_initialize_azure_blob_service_client_missing_account_name(self):
		"""Test that ValueError is raised when account name is missing."""
		from ai_ticket_platform.core.clients.azure import (
			initialize_azure_blob_service_client,
		)

		with patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT_KEY": "testkey123"}):
			# Reset global client
			import ai_ticket_platform.core.clients.azure as azure_module

			azure_module.blob_service_client = None

			with pytest.raises(ValueError) as exc_info:
				initialize_azure_blob_service_client()

			assert "Azure Blob Storage credentials not found" in str(exc_info.value)

	def test_initialize_azure_blob_service_client_missing_account_key(self):
		"""Test that ValueError is raised when account key is missing."""
		from ai_ticket_platform.core.clients.azure import (
			initialize_azure_blob_service_client,
		)

		with patch.dict("os.environ", {"AZURE_STORAGE_ACCOUNT_NAME": "testaccount"}):
			# Reset global client
			import ai_ticket_platform.core.clients.azure as azure_module

			azure_module.blob_service_client = None

			with pytest.raises(ValueError) as exc_info:
				initialize_azure_blob_service_client()

			assert "Azure Blob Storage credentials not found" in str(exc_info.value)
