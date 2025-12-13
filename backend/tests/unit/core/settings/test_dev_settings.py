"""Unit tests for DevSettings class."""

from unittest.mock import patch


class TestDevSettingsRequiredVars:
	"""Test required_vars property with different cloud providers."""

	def test_required_vars_with_aws(self):
		"""Test required_vars includes AWS-specific variables."""
		from ai_ticket_platform.core.settings.environment.dev import DevSettings

		with patch.dict(
			"os.environ",
			{"CLOUD_PROVIDER": "aws"},
			clear=False,
		):
			settings = DevSettings()
			required = settings.required_vars

			assert "S3_MAIN_BUCKET_NAME" in required
			assert "AWS_MAIN_REGION" in required
			assert "AZURE_STORAGE_CONTAINER_NAME" not in required

	def test_required_vars_with_azure(self):
		"""Test required_vars includes Azure-specific variables."""
		from ai_ticket_platform.core.settings.environment.dev import DevSettings

		with patch.dict(
			"os.environ",
			{"CLOUD_PROVIDER": "azure"},
			clear=False,
		):
			settings = DevSettings()
			required = settings.required_vars

			assert "AZURE_STORAGE_CONTAINER_NAME" in required
			assert "AZURE_STORAGE_ACCOUNT_NAME" in required
			assert "AZURE_STORAGE_ACCOUNT_KEY" in required
			assert "S3_MAIN_BUCKET_NAME" not in required


class TestDevSettingsExtraction:
	"""Test variable extraction methods."""

	def test_extract_storage_variables_azure(self):
		"""Test extracting Azure storage variables."""
		from ai_ticket_platform.core.settings.environment.dev import DevSettings

		with patch.dict(
			"os.environ",
			{
				"CLOUD_PROVIDER": "azure",
				"AZURE_STORAGE_CONTAINER_NAME": "test-container",
				"AZURE_STORAGE_ACCOUNT_NAME": "testaccount",
				"AZURE_STORAGE_ACCOUNT_KEY": "testkey123",
			},
			clear=False,
		):
			settings = DevSettings()
			settings.CLOUD_PROVIDER = "azure"
			settings._extract_storage_variables()

			assert settings.AZURE_STORAGE_CONTAINER_NAME == "test-container"
			assert settings.AZURE_STORAGE_ACCOUNT_NAME == "testaccount"
			assert settings.AZURE_STORAGE_ACCOUNT_KEY == "testkey123"
