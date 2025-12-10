import logging
from enum import Enum
from typing import Optional, Union

from botocore.exceptions import ClientError

from .storage import StorageService

logger = logging.getLogger(__name__)


class PresignedUrlActionsType(Enum):
	PUT = "put_object"
	GET = "get_object"


class AWSS3Storage(StorageService):
	"""AWS S3 storage implementation."""

	def __init__(self, bucket_name: str):
		from ai_ticket_platform.core.clients.aws import initialize_aws_s3_client

		self.bucket_name = bucket_name
		self._s3_client = initialize_aws_s3_client()

	def _generate_url(
		self,
		action_type: PresignedUrlActionsType,
		key: str,
		expiration_time_secs: int = 3600,
		verify_exists: bool = True,
		**kwargs,
	):
		try:
			if verify_exists and action_type == PresignedUrlActionsType.GET:
				try:
					self._s3_client.head_object(Bucket=self.bucket_name, Key=key)
				except ClientError as e:
					error_code = e.response["Error"]["Code"]
					if error_code == "404":
						raise ValueError(
							f"Object not found in S3: s3://{self.bucket_name}/{key}"
						)
					raise

			presigned_url = self._s3_client.generate_presigned_url(
				ClientMethod=action_type.value,
				Params={"Bucket": self.bucket_name, "Key": key, **kwargs},
				ExpiresIn=expiration_time_secs,
			)
			logger.info("Presigned url generated successfully")
			return presigned_url
		except Exception as e:
			logger.exception("Exception occurred while generating presigned URL")
			raise

	def get_presigned_url(
		self,
		file_path: str,
		expiration_time_secs: int = 3600,
		content_type: Optional[str] = None,
		**kwargs,
	) -> str:
		params = {}
		if content_type:
			params["ContentType"] = content_type
		params.update(kwargs)

		return self._generate_url(
			action_type=PresignedUrlActionsType.GET,
			key=file_path,
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
		params = {}
		if content_type:
			params["ContentType"] = content_type
		params.update(kwargs)

		return self._generate_url(
			action_type=PresignedUrlActionsType.PUT,
			key=file_path,
			expiration_time_secs=expiration_time_secs,
			verify_exists=False,
			**params,
		)

	def upload_blob(
		self,
		blob_name: str,
		content: Union[str, bytes],
		content_type: Optional[str] = None,
	) -> str:
		"""
		Upload content (string or binary) directly to S3 using backend credentials.

		Args:
		    blob_name: S3 key/path of the object
		    content: String or binary content to upload
		    content_type: Optional MIME type (e.g., 'text/markdown')

		Returns:
		    The S3 key of the uploaded object
		"""
		try:
			upload_kwargs = {}
			if content_type:
				upload_kwargs["ContentType"] = content_type

			# Convert string to bytes if needed
			if isinstance(content, str):
				content = content.encode('utf-8')

			self._s3_client.put_object(
				Bucket=self.bucket_name,
				Key=blob_name,
				Body=content,
				**upload_kwargs
			)
			logger.info(f"Successfully uploaded to S3: s3://{self.bucket_name}/{blob_name}")
			return blob_name
		except Exception as e:
			logger.error(f"Failed to upload to S3 {blob_name}: {e}", exc_info=True)
			raise

	def download_blob(self, blob_name: str, decode: bool = True) -> Union[str, bytes]:
		"""
		Download content from S3.

		Args:
		    blob_name: S3 key/path of the object
		    decode: If True, decode content as UTF-8 string; if False, return raw bytes

		Returns:
		    String content (if decode=True) or bytes (if decode=False)
		"""
		try:
			response = self._s3_client.get_object(
				Bucket=self.bucket_name,
				Key=blob_name
			)
			content = response['Body'].read()
			logger.info(f"Successfully downloaded from S3: s3://{self.bucket_name}/{blob_name}")
			return content.decode('utf-8') if decode else content
		except ClientError as e:
			logger.error(f"Failed to download from S3 {blob_name}: {e}", exc_info=True)
			raise
