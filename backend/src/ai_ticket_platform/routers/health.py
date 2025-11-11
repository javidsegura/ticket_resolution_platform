from typing import Annotated, Dict

from fastapi import APIRouter, Depends, Request, status

from ai_ticket_platform.core.clients.utils.check_clients_connection import check_db_connection, check_redis_connection
from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.dependencies import get_app_settings, get_db
from ai_ticket_platform.database.CRUD.user import read_user

from ai_ticket_platform.core.settings import Settings

import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/health")

# Health
@router.get(path="/dependencies", status_code=status.HTTP_200_OK)
async def cheeck_backend_health_dependencies_endpoint(
	db: Annotated[AsyncSession, Depends(get_db)],
) -> Dict:
	"""
	You could have here the response schema to be service with variables\
		being 'status' and 'error' (if any)
	"""
	redis_status = await check_redis_connection()
	db_status = await check_db_connection(db=db)
	return {"services": { 
				  "redis": redis_status,
				   "db": db_status}} 

@router.get(path="/ping", status_code=status.HTTP_200_OK)
async def cheeck_backend_health_endpoint(
) -> Dict:
	return {"response": "pong"}
