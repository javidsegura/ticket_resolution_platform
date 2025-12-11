"""
Test router for S3 presigned URL operations.
This is a temporary router for testing S3 upload/download functionality.
"""

import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/s3-test", tags=["S3 Test"])


@router.get("/presigned-url/upload", status_code=status.HTTP_200_OK)
async def get_upload_presigned_url(
	file_path: str = Query(..., description="S3 key/path for the file"),
	content_type: Optional[str] = Query(
		None, description="Content type of the file (e.g., image/png, application/pdf)"
	),
	expiration: int = Query(
		3600, description="URL expiration time in seconds", ge=60, le=604800
	),
):
	"""
	Generate a presigned URL for uploading a file to S3.

	Usage:
	1. Call this endpoint to get a presigned URL
	2. Use the returned URL to PUT your file directly to S3 using curl or any HTTP client

	Example:
	```bash
	# Get the presigned URL
	curl "http://localhost:8000/api/s3-test/presigned-url/upload?file_path=test/myfile.jpg&content_type=image/jpeg"

	# Upload a file using the presigned URL
	curl -X PUT -H "Content-Type: image/jpeg" --upload-file myfile.jpg "<presigned_url>"
	```
	"""
	try:
		from ai_ticket_platform.services.infra.storage.aws import AWSS3Storage

		bucket_name = os.getenv("S3_MAIN_BUCKET_NAME")
		if not bucket_name:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail="AWS_S3_BUCKET_NAME environment variable not set",
			)

		storage = AWSS3Storage(bucket_name=bucket_name)
		presigned_url = storage.put_presigned_url(
			file_path=file_path,
			expiration_time_secs=expiration,
			content_type=content_type,
		)

		return {
			"presigned_url": presigned_url,
			"file_path": file_path,
			"bucket": bucket_name,
			"expiration_seconds": expiration,
			"method": "PUT",
			"instructions": {
				"curl": f'curl -X PUT -H "Content-Type: {content_type or "application/octet-stream"}" --upload-file <local_file> "{presigned_url}"',
				"note": "Replace <local_file> with your actual file path",
			},
		}
	except Exception as e:
		logger.exception("Failed to generate upload presigned URL")
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to generate presigned URL: {str(e)}",
		)


@router.get("/presigned-url/download", status_code=status.HTTP_200_OK)
async def get_download_presigned_url(
	file_path: str = Query(..., description="S3 key/path for the file"),
	expiration: int = Query(
		3600, description="URL expiration time in seconds", ge=60, le=604800
	),
):
	"""
	Generate a presigned URL for downloading a file from S3.

	Usage:
	1. Call this endpoint to get a presigned URL
	2. Use the returned URL to GET your file directly from S3

	Example:
	```bash
	# Get the presigned URL
	curl "http://localhost:8000/api/s3-test/presigned-url/download?file_path=test/myfile.jpg"

	# Download the file using the presigned URL
	curl -o downloaded_file.jpg "<presigned_url>"
	```
	"""
	try:
		from ai_ticket_platform.services.storage.aws import AWSS3Storage

		bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
		if not bucket_name:
			raise HTTPException(
				status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
				detail="AWS_S3_BUCKET_NAME environment variable not set",
			)

		storage = AWSS3Storage(bucket_name=bucket_name)
		presigned_url = storage.get_presigned_url(
			file_path=file_path, expiration_time_secs=expiration
		)

		return {
			"presigned_url": presigned_url,
			"file_path": file_path,
			"bucket": bucket_name,
			"expiration_seconds": expiration,
			"method": "GET",
			"instructions": {
				"curl": f'curl -o downloaded_file "{presigned_url}"',
				"browser": "You can also paste the URL directly in your browser",
			},
		}
	except ValueError as e:
		# File not found in S3
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
	except Exception as e:
		logger.exception("Failed to generate download presigned URL")
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Failed to generate presigned URL: {str(e)}",
		)


@router.get("/bucket-info", status_code=status.HTTP_200_OK)
async def get_bucket_info():
	"""
	Get information about the configured S3 bucket.
	"""
	bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
	region = os.getenv("AWS_MAIN_REGION")

	if not bucket_name:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="AWS_S3_BUCKET_NAME environment variable not set",
		)

	return {"bucket_name": bucket_name, "region": region, "status": "configured"}
