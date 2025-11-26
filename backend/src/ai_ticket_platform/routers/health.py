import asyncio
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status

from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.dependencies import get_app_settings, get_db

from ai_ticket_platform.core.settings import Settings
from ai_ticket_platform.core.clients import initialize_redis_client

import logging

logger = logging.getLogger(__name__)
from ai_ticket_platform.core.clients.utils.check_clients_connection import test_redis_connection, test_db_connection


router = APIRouter(prefix="/health")

# Health
# @router.get(path="/dependencies", status_code=status.HTTP_200_OK)
# async def cheeck_backend_health_dependencies_endpoint(
# 	db: Annotated[AsyncSession, Depends(get_db)],
# 	settings: Annotated[list, Depends(get_app_settings)]
# ) -> Dict:
# 	"""
# 	You could have here the response schema to be service with variables\
# 		being 'status' and 'error' (if any)
# 	"""
# 	"""
# 	Simple readiness probe that only returns 200 when all dependencies are OK.
# 	"""


# 	checks = {"status": "healthy", "checks": {}}

# 	print("Aaaaaaaaqa")
    
# 	# Redis
# 	try:
# 		redis_connected = await test_redis_connection()
# 		if not redis_connected:
# 			raise Exception()
# 		checks["checks"]["redis"] = "ok"
# 	except Exception as e:
# 		checks["status"] = "unhealthy"
# 		checks["checks"]["redis"] = f"failed: {e}"
	
# 	# Workers
# 	try:
# 		# RQ requires a synchronous Redis connection, not async
# 		# RQ is a synchronous library and cannot use async Redis clients
# 		redis_client_connector = initialize_redis_client()
# 		sync_redis_connection = redis_client_connector.get_sync_connection()
# 		workers = Worker.all(connection=sync_redis_connection)
# 		count = len(workers)
# 		checks["checks"]["workers"] = f"{count} active"
# 		if count == 0:
# 			checks["status"] = "degraded"
# 	except Exception as e:
# 		checks["status"] = "unhealthy"
# 		checks["checks"]["workers"] = f"failed: {e}"
	
# 	if checks["status"] == "unhealthy":
# 		raise HTTPException(
# 			status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
# 			detail=checks,
# 		)
	
# 	return checks


@router.get(path="/ping", status_code=status.HTTP_200_OK)
async def cheeck_backend_health_endpoint(
) -> Dict:
	return {"response": "pong"}
