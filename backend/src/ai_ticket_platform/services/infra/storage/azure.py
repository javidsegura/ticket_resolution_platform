import logging
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Union

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobSasPermissions, generate_blob_sas, ContentSettings

from .storage import StorageService

logger = logging.getLogger(__name__)


class SasUrlActionsType(Enum):
	PUT = "write"
	GET = "read"


class AzureBlobStorage(StorageService):
	"""Azure Blob Storage implementation."""

	def __init__(self, container_name: str):
		from ai_ticket_platform.core.clients.azure import (
			initialize_azure_blob_service_client,
		)

		self.container_name = container_name
		self._blob_service_client = initialize_azure_blob_service_client()
		self._account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
		self._account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")

	def _generate_url(
		self,
		action_type: SasUrlActionsType,
		blob_name: str,
		expiration_time_secs: int = 3600,
		verify_exists: bool = True,
		**kwargs,
	):
		try:
			if verify_exists and action_type == SasUrlActionsType.GET:
				try:
					blob_client = self._blob_service_client.get_blob_client(
						container=self.container_name, blob=blob_name
					)
					blob_client.get_blob_properties()
				except ResourceNotFoundError:
					raise ValueError(
						f"Blob not found in Azure Storage: {self.container_name}/{blob_name}"
					)

			if action_type == SasUrlActionsType.GET:
				permissions = BlobSasPermissions(read=True)
			else:
				permissions = BlobSasPermissions(write=True, create=True)

			expiry_time = datetime.utcnow() + timedelta(seconds=expiration_time_secs)

			sas_token = generate_blob_sas(
				account_name=self._account_name,
				container_name=self.container_name,
				blob_name=blob_name,
				account_key=self._account_key,
				permission=permissions,
				expiry=expiry_time,
				**kwargs,
			)

			blob_url = f"https://{self._account_name}.blob.core.windows.net/{self.container_name}/{blob_name}?{sas_token}"

			logger.info("SAS URL generated successfully")
			return blob_url
		except Exception as e:
			logger.exception("Exception occurred while generating SAS URL")
			raise

	def get_presigned_url(
		self,
		file_path: str,
		expiration_time_secs: int = 3600,
		content_type: Optional[str] = None,
		**kwargs,
	) -> str:
		# Note: content_type is not used in Azure SAS generation
		# Content-Type is determined by the blob's properties set during upload
		params = {}
		params.update(kwargs)

		return self._generate_url(
			action_type=SasUrlActionsType.GET,
			blob_name=file_path,
			expiration_time_secs=expiration_time_secs,
			**params,
		)

	def put_presigned_url(
		self,
		file_path: str,
		expiration_time_secs: int = 3600,
		content_type: Optional[str] = None,
		**kwargs,
	) -> str:
		# Note: content_type is not used in Azure SAS generation
		# The client uploading should set Content-Type header instead
		params = {}
		params.update(kwargs)

		return self._generate_url(
			action_type=SasUrlActionsType.PUT,
			blob_name=file_path,
			expiration_time_secs=expiration_time_secs,
			verify_exists=False,
			**params,
		)

	def upload_blob(self, blob_name: str, content: Union[str, bytes], content_type: Optional[str] = None) -> str:
		"""
		Upload content (string or binary) directly to Azure Blob Storage using backend credentials.

		Args:
		    blob_name: Name/path of the blob
		    content: String or binary content to upload
		    content_type: Optional MIME type (e.g., 'application/pdf')

		Returns:
		    blob_name (for consistency with expected return value)
		"""
		try:
			blob_client = self._blob_service_client.get_blob_client(
				container=self.container_name, blob=blob_name
			)
			upload_kwargs = {"overwrite": True}
			if content_type:
				upload_kwargs["content_settings"] = ContentSettings(content_type=content_type)

			blob_client.upload_blob(content, **upload_kwargs)
			logger.info(f"Successfully uploaded blob: {self.container_name}/{blob_name}")
			return blob_name
		except Exception as e:
			logger.error(f"Failed to upload blob {blob_name}: {e}", exc_info=True)
			raise

	def download_blob(self, blob_name: str) -> str:
		"""
		Download content from Azure Blob Storage.

		Args:
		    blob_name: Name/path of the blob

		Returns:
		    String content of the blob
		"""
		try:
			blob_client = self._blob_service_client.get_blob_client(
				container=self.container_name, blob=blob_name
			)
			download_stream = blob_client.download_blob()
			content = download_stream.readall()
			logger.info(f"Successfully downloaded blob: {self.container_name}/{blob_name}")
			return content.decode('utf-8')
		except Exception as e:
			logger.error(f"Failed to download blob {blob_name}: {e}", exc_info=True)
			raise
