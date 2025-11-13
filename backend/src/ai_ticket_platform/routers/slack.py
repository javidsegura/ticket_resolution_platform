from typing import Annotated, Dict

from fastapi import APIRouter, Depends, Request, status

from ai_ticket_platform.core.clients.utils.check_clients_connection import check_db_connection, check_redis_connection
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.dependencies import get_app_settings, get_db

from ai_ticket_platform.core.settings import Settings

import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/slack")

# Health
@router.post(path="/receive-answer", status_code=status.HTTP_200_OK)
async def cheeck_backend_health_dependencies_endpoint()
	""""""
    pass

@router.get(path="/ping", status_code=status.HTTP_200_OK)
async def cheeck_backend_health_endpoint(
) -> Dict:
	return {"response": "pong"}
