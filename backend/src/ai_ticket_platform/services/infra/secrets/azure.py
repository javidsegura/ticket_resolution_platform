import json
import logging
from typing import Any, Dict

from azure.core.exceptions import HttpResponseError, ResourceNotFoundError

from .secrets import SecretsService

logger = logging.getLogger(__name__)


class AzureKeyVault(SecretsService):
	"""Azure Key Vault implementation."""

	def __init__(self, vault_name: str):
		try:
			from azure.identity import DefaultAzureCredential
			from azure.keyvault.secrets import SecretClient
		except ImportError:
			raise ImportError(
				"Azure Key Vault libraries not installed. "
				"Install with: pip install azure-keyvault-secrets azure-identity"
			)

		self.vault_name = vault_name
		vault_url = f"https://{vault_name}.vault.azure.net"

		# Authenticate using DefaultAzureCredential (works with managed identity, CLI, env vars, etc.)
		credential = DefaultAzureCredential()

		# Create SecretClient
		self._secret_client = SecretClient(vault_url=vault_url, credential=credential)
		logger.debug(f"Initialized Azure Key Vault client for: {vault_name}")

	def fetch_secret(self, secret_key: str) -> Dict[str, Any]:
		"""
		Fetch a secret from Azure Key Vault.

		Args:
		    secret_key: The secret name in the Key Vault

		Returns:
		    Dictionary containing the secret data (JSON-parsed if possible)

		Raises:
		    ValueError: If secret is not found or cannot be accessed
		"""
		try:
			logger.debug(f"Fetching secret: {secret_key} from vault: {self.vault_name}")
			secret = self._secret_client.get_secret(secret_key)

			if secret.value:
				try:
					# Try to parse as JSON (credentials are typically stored as JSON)
					parsed_secret = json.loads(secret.value)
					logger.info(f"Successfully fetched and parsed secret: {secret_key}")
					return parsed_secret
				except json.JSONDecodeError:
					# If not JSON, return as plain value
					logger.warning(
						f"Secret {secret_key} is not JSON, returning as plain value"
					)
					return {"value": secret.value}
			else:
				raise ValueError(f"Secret {secret_key} has no value")
		except ResourceNotFoundError:
			raise ValueError(
				f"Secret {secret_key} not found in Azure Key Vault: {self.vault_name}"
			)
		except HttpResponseError as e:
			if e.status_code == 403:
				raise ValueError(
					f"Access denied to secret {secret_key} in vault {self.vault_name}"
				)
			else:
				logger.exception(f"HTTP error fetching secret {secret_key}")
				raise
		except Exception as e:
			logger.exception(f"Exception occurred while fetching secret {secret_key}")
			raise
