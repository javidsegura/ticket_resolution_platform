"""Unit tests for AWS client initialization."""

from unittest.mock import patch, MagicMock


class TestInitializeAWSS3Client:
	"""Test initialize_aws_s3_client function."""

	@patch("ai_ticket_platform.core.clients.aws.boto3.client")
	def test_initialize_aws_s3_client_first_time(self, mock_boto_client):
		"""Test S3 client initialization for the first time."""
		from ai_ticket_platform.core.clients.aws import initialize_aws_s3_client
		import ai_ticket_platform.core.clients.aws as aws_module

		# Reset global
		aws_module.s3_client = None

		mock_client = MagicMock()
		mock_boto_client.return_value = mock_client

		with patch.dict("os.environ", {"AWS_MAIN_REGION": "us-east-1"}):
			result = initialize_aws_s3_client()

			assert result == mock_client
			mock_boto_client.assert_called_once_with("s3", region_name="us-east-1")
			assert aws_module.s3_client == mock_client

	@patch("ai_ticket_platform.core.clients.aws.boto3.client")
	def test_initialize_aws_s3_client_returns_existing(self, mock_boto_client):
		"""Test that existing S3 client is returned."""
		from ai_ticket_platform.core.clients.aws import initialize_aws_s3_client
		import ai_ticket_platform.core.clients.aws as aws_module

		mock_existing = MagicMock()
		aws_module.s3_client = mock_existing

		result = initialize_aws_s3_client()

		assert result == mock_existing
		mock_boto_client.assert_not_called()


class TestInitializeAWSSecretsManagerClient:
	"""Test initialize_aws_secrets_manager_client function."""

	@patch("ai_ticket_platform.core.clients.aws.boto3.client")
	def test_initialize_secrets_manager_client_first_time(self, mock_boto_client):
		"""Test Secrets Manager client initialization for the first time."""
		from ai_ticket_platform.core.clients.aws import (
			initialize_aws_secrets_manager_client,
		)
		import ai_ticket_platform.core.clients.aws as aws_module

		# Reset global
		aws_module.secrets_manager_client = None

		mock_client = MagicMock()
		mock_boto_client.return_value = mock_client

		with patch.dict("os.environ", {"AWS_MAIN_REGION": "us-west-2"}):
			result = initialize_aws_secrets_manager_client()

			assert result == mock_client
			mock_boto_client.assert_called_once_with(
				"secretsmanager", region_name="us-west-2"
			)
			assert aws_module.secrets_manager_client == mock_client

	@patch("ai_ticket_platform.core.clients.aws.boto3.client")
	def test_initialize_secrets_manager_client_returns_existing(self, mock_boto_client):
		"""Test that existing Secrets Manager client is returned."""
		from ai_ticket_platform.core.clients.aws import (
			initialize_aws_secrets_manager_client,
		)
		import ai_ticket_platform.core.clients.aws as aws_module

		mock_existing = MagicMock()
		aws_module.secrets_manager_client = mock_existing

		result = initialize_aws_secrets_manager_client()

		assert result == mock_existing
		mock_boto_client.assert_not_called()
