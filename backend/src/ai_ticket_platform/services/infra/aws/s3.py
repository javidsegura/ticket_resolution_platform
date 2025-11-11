from enum import Enum
from botocore.exceptions import ClientError
from mypy_boto3_s3.client import S3Client
from ai_ticket_platform.core.clients.aws import initialize_aws_s3_client


class PresignedUrlActionsType(Enum):
      PUT =  "put_object"
      GET = "get_object" 

import logging

logger = logging.getLogger(__name__)

class PresignedUrl():
      def __init__(self) -> None:
           self._s3_client = initialize_aws_s3_client()
      
      def _generate_url(self, action_type: PresignedUrlActionsType,
                      s3_bucket_name: str,
                      key: str,
                      expiration_time_secs:int = 3600,
                      verify_exists: bool = True,  
                      **kwargs):
        try:
            if verify_exists and action_type == PresignedUrlActionsType.GET:
                try:
                    self._s3_client.head_object(Bucket=s3_bucket_name, Key=key)
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    if error_code == '404':
                        raise ValueError(f"Object not found in S3: s3://{s3_bucket_name}/{key}")
                    raise
            
            presigned_url = self._s3_client.generate_presigned_url(
                ClientMethod=action_type.value,
                Params={
                    "Bucket": s3_bucket_name,
                    "Key": key,
                    **{str(k): v for k, v in kwargs.items()}  # Fixed variable name collision
                },
                ExpiresIn=expiration_time_secs
            )
            logger.info("Presigned url extracted successfully")
            return presigned_url
        except Exception as e:
            logger.exception("Exception occurred while generating presigned URL")
            raise
      def get_presigned_url(self, s3_bucket_name: str, key: str, expiration_time_secs:int = 3600, **kwargs) -> str:
            return self._generate_url(
                  action_type=PresignedUrlActionsType.GET,
                  s3_bucket_name=s3_bucket_name,
                  key=key,
                  expiration_time_secs=expiration_time_secs,
                  **kwargs
            )
      def put_presigned_url(self, s3_bucket_name: str, key: str, expiration_time_secs:int = 3600, **kwargs) -> str:
            return self._generate_url(
                  action_type=PresignedUrlActionsType.PUT,
                  s3_bucket_name=s3_bucket_name,
                  key=key,
                  expiration_time_secs=expiration_time_secs,
                  **kwargs
            )

