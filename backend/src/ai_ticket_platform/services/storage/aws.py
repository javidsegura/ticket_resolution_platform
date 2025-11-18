from typing import Optional
from enum import Enum
from botocore.exceptions import ClientError
import logging

from .storage import StorageService

logger = logging.getLogger(__name__)


class PresignedUrlActionsType(Enum):
    PUT = "put_object"
    GET = "get_object"


class AWSS3Storage(StorageService):
    """AWS S3 storage implementation."""
    
    def __init__(self, bucket_name: str):
        from url_shortener.core.clients.aws import initialize_aws_s3_client
        self.bucket_name = bucket_name
        self._s3_client = initialize_aws_s3_client()
    
    def _generate_url(
        self,
        action_type: PresignedUrlActionsType,
        key: str,
        expiration_time_secs: int = 3600,
        verify_exists: bool = True,
        **kwargs
    ):
        try:
            if verify_exists and action_type == PresignedUrlActionsType.GET:
                try:
                    self._s3_client.head_object(Bucket=self.bucket_name, Key=key)
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == '404':
                        raise ValueError(f"Object not found in S3: s3://{self.bucket_name}/{key}")
                    raise
            
            presigned_url = self._s3_client.generate_presigned_url(
                ClientMethod=action_type.value,
                Params={
                    "Bucket": self.bucket_name,
                    "Key": key,
                    **kwargs
                },
                ExpiresIn=expiration_time_secs
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
        **kwargs
    ) -> str:
        params = {}
        if content_type:
            params['ContentType'] = content_type
        params.update(kwargs)
        
        return self._generate_url(
            action_type=PresignedUrlActionsType.GET,
            key=file_path,
            expiration_time_secs=expiration_time_secs,
            **params
        )
    
    def put_presigned_url(
        self,
        file_path: str,
        expiration_time_secs: int = 3600,
        content_type: Optional[str] = None,
        **kwargs
    ) -> str:
        params = {}
        if content_type:
            params['ContentType'] = content_type
        params.update(kwargs)
        
        return self._generate_url(
            action_type=PresignedUrlActionsType.PUT,
            key=file_path,
            expiration_time_secs=expiration_time_secs,
            verify_exists=False,
            **params
        )

