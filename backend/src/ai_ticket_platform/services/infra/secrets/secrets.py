import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class SecretsService(ABC):
	"""
	Cloud-agnostic secrets service interface.
	Abstracts away AWS Secrets Manager vs Azure Key Vault differences.
	"""

	@abstractmethod
	def fetch_secret(self, secret_key: str) -> Dict[str, Any]:
		"""
		Fetch a secret from the cloud provider's secrets management service.

		Args:
		    secret_key: The identifier for the secret (secret name/ARN for AWS, secret name for Azure)

		Returns:
		    Dictionary containing the secret data (typically JSON-parsed)

		Raises:
		    ValueError: If secret is not found or cannot be parsed
		"""
		pass


def get_secrets_service() -> SecretsService:
	"""
	Factory function to get the appropriate secrets service based on configuration.

	Environment variables:
	- CLOUD_PROVIDER: 'aws' or 'azure' (defaults to 'aws')
	- AWS_MAIN_REGION: For AWS (required for AWS)
	- AZURE_KEY_VAULT_NAME: For Azure (required for Azure)
	"""
	from .aws import AWSSecretsManager
	from .azure import AzureKeyVault

	cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()

	if cloud_provider == "azure":
		vault_name = os.getenv("AZURE_KEY_VAULT_NAME")
		if not vault_name:
			raise ValueError("AZURE_KEY_VAULT_NAME not set")
		logger.info(f"Using Azure Key Vault: {vault_name}")
		return AzureKeyVault(vault_name=vault_name)
	else:
		region_name = os.getenv("AWS_MAIN_REGION")
		if not region_name:
			raise ValueError("AWS_MAIN_REGION not set")
		logger.info(f"Using AWS Secrets Manager in region: {region_name}")
		return AWSSecretsManager(region_name=region_name)
