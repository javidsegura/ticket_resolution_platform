import json
import logging
from typing import Any, Dict

from botocore.exceptions import ClientError

from .secrets import SecretsService

logger = logging.getLogger(__name__)


class AWSSecretsManager(SecretsService):
	"""AWS Secrets Manager implementation."""

	def __init__(self, region_name: str):
		from ai_ticket_platform.core.clients.aws import (
			initialize_aws_secrets_manager_client,
		)

		self.region_name = region_name
		self._secrets_client = initialize_aws_secrets_manager_client()

	def fetch_secret(self, secret_key: str) -> Dict[str, Any]:
		"""
		Fetch a secret from AWS Secrets Manager.

		Args:
		    secret_key: The secret name or ARN

		Returns:
		    Dictionary containing the secret data (JSON-parsed if possible)

		Raises:
		    ValueError: If secret is not found or doesn't have a SecretString
		"""
		try:
			logger.debug(f"Fetching secret: {secret_key}")
			get_secret_value_response = self._secrets_client.get_secret_value(
				SecretId=secret_key
			)

			if "SecretString" in get_secret_value_response:
				secret_value = get_secret_value_response["SecretString"]
				try:
					# Try to parse as JSON (credentials are typically stored as JSON)
					parsed_secret = json.loads(secret_value)
					logger.info(f"Successfully fetched and parsed secret: {secret_key}")
					return parsed_secret
				except json.JSONDecodeError:
					# If not JSON, return as plain value
					logger.warning(
						f"Secret {secret_key} is not JSON, returning as plain value"
					)
					return {"value": secret_value}
			else:
				raise ValueError(
					f"Secret {secret_key} doesn't have a Secret string. "
					"Binary secrets are not supported."
				)
		except ClientError as e:
			error_code = e.response["Error"]["Code"]
			if error_code == "ResourceNotFoundException":
				raise ValueError(
					f"Secret {secret_key} not found in AWS Secrets Manager"
				)
			elif error_code == "AccessDeniedException":
				raise ValueError(f"Access denied to secret {secret_key}")
			else:
				logger.exception(f"Error fetching secret {secret_key}")
				raise
		except Exception as e:
			logger.exception(f"Exception occurred while fetching secret {secret_key}")
			raise
