from typing import Annotated
from fastapi import Depends
from url_shortener.services.storage.storage import StorageService, get_storage_service


def get_storage_service_dependency() -> StorageService:
    """FastAPI dependency to get the configured storage service."""
    return get_storage_service()

