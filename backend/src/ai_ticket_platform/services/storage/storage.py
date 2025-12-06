from abc import ABC, abstractmethod
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


class StorageService(ABC):
	"""
	Cloud-agnostic storage service interface for presigned URLs.
	Abstracts away AWS S3 vs Azure Blob Storage differences.
	"""

	@abstractmethod
	def get_presigned_url(
		self,
		file_path: str,
		expiration_time_secs: int = 3600,
		content_type: Optional[str] = None,
		**kwargs,
	) -> str:
		"""Generate a presigned URL for downloading/reading a file."""
		pass

	@abstractmethod
	def put_presigned_url(
		self,
		file_path: str,
		expiration_time_secs: int = 3600,
		content_type: Optional[str] = None,
		**kwargs,
	) -> str:
		"""Generate a presigned URL for uploading/writing a file."""
		pass


def get_storage_service() -> StorageService:
	"""
	Factory function to get the appropriate storage service based on configuration.

	Environment variables:
	- CLOUD_PROVIDER: 'aws' or 'azure' (defaults to 'aws')
	- S3_MAIN_BUCKET_NAME: For AWS
	- AZURE_STORAGE_CONTAINER_NAME: For Azure
	"""
	from .aws import AWSS3Storage
	from .azure import AzureBlobStorage

	cloud_provider = os.getenv("CLOUD_PROVIDER", "aws").lower()

	if cloud_provider == "azure":
		container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")
		if not container_name:
			raise ValueError("AZURE_STORAGE_CONTAINER_NAME not set")
		logger.info(f"Using Azure Blob Storage with container: {container_name}")
		return AzureBlobStorage(container_name=container_name)
	else:
		bucket_name = os.getenv("S3_MAIN_BUCKET_NAME")
		if not bucket_name:
			raise ValueError("S3_MAIN_BUCKET_NAME not set")
		logger.info(f"Using AWS S3 with bucket: {bucket_name}")
		return AWSS3Storage(bucket_name=bucket_name)
