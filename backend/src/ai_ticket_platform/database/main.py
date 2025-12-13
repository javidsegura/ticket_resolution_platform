# database.py - Production-ready database configuration
import os
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ai_ticket_platform.core.settings.app_settings import initialize_settings

AsyncSessionLocal = None


def initialize_db_engine():
	# No need to change this
	global AsyncSessionLocal
	app_settings = initialize_settings()

	if not AsyncSessionLocal:
		DATABASE_URL = (
			f"{app_settings.MYSQL_ASYNC_DRIVER}"
			f"://{app_settings.MYSQL_USER}:{app_settings.MYSQL_PASSWORD}@{app_settings.MYSQL_HOST}"
			f":{app_settings.MYSQL_PORT}/{app_settings.MYSQL_DATABASE}"
		)

		# Use NullPool in test environment to avoid event loop issues
		# In test, each pytest test runs in its own event loop, so connection pooling
		# causes "Future attached to a different loop" errors
		environment = os.getenv("ENVIRONMENT", "").lower()

		if environment == "test":
			from sqlalchemy.pool import NullPool

			engine = create_async_engine(
				DATABASE_URL,
				echo=False,
				poolclass=NullPool,  # No connection pooling in test
			)
		else:
			# Production engine configuration with connection pooling
			engine = create_async_engine(
				DATABASE_URL,
				echo=False,  # Never True in production (performance impact)
				pool_size=10,  # Connection pool size
				max_overflow=20,  # Additional connections when pool is full
				pool_pre_ping=True,  # Validate connections before use
				pool_recycle=3600,  # Recycle connections every hour
			)

		AsyncSessionLocal = async_sessionmaker(
			engine, class_=AsyncSession, expire_on_commit=False
		)
	return AsyncSessionLocal
