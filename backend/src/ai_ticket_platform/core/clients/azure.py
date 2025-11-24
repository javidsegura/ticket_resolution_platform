from azure.storage.blob import BlobServiceClient
import os
import logging

logger = logging.getLogger(__name__)

blob_service_client = None


def initialize_azure_blob_service_client():
    global blob_service_client
    logger.debug("Initializing Azure Blob Service client")
    if not blob_service_client:
        logger.debug("Instantiating blob service client for the first time")
        account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        
        if not account_name or not account_key:
            raise ValueError(
                "Azure Blob Storage credentials not found. "
                "Set AZURE_STORAGE_ACCOUNT_NAME and AZURE_STORAGE_ACCOUNT_KEY"
            )
        
        account_url = f"https://{account_name}.blob.core.windows.net"
        blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=account_key
        )
    return blob_service_client

