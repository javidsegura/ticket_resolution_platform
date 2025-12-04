from typing import Annotated
from fastapi import Depends
from ai_ticket_platform.services.infra.storage.storage import (
	StorageService,
	get_storage_service,
)


def get_storage_service_dependency() -> StorageService:
	"""FastAPI dependency to get the configured storage service."""
	return get_storage_service()
