from sqlalchemy.ext.asyncio import AsyncSession
from ai_ticket_platform.database.main import initialize_db_engine

# DONT CHANGE THIS SECTION


async def get_db() -> AsyncSession:
	AsyncSessionLocal = initialize_db_engine()
	async with AsyncSessionLocal() as session:
		try:
			yield session
		finally:
			await session.close()
