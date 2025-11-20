from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select  # Important for async queries

from ai_ticket_platform.core.clients.redis import initialize_redis_client
from ai_ticket_platform.dependencies import get_db
from ai_ticket_platform.database import User

# Redis
async def test_redis_connection() -> bool:
	redis_client_connector = initialize_redis_client()
	client = await redis_client_connector.get_client()
	response = await client.ping()
	return bool(response)


# Database
async def test_db_connection(db: AsyncSession = Depends(get_db)) -> bool:
	try:
		await db.execute(text("SELECT 1"))
		return True
	except Exception:
		return False
