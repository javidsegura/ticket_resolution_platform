"""
Integration test conftest

Provides async HTTP client to test the running backend via ASGI transport.
Tests validate E2E behavior of the MVP pipeline without a separate test database.
"""

import pytest
import pytest_asyncio
import os
import logging
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import redis.asyncio as redis

from ai_ticket_platform.main import app

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def async_client():
	"""
	Provide an async HTTP client to the running backend server.
	Uses ASGI transport for testing without real HTTP server.
	"""
	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test") as client:
		yield client


@pytest_asyncio.fixture
async def db_connection():
	"""
	Provide a direct async database connection for verification queries.
	Uses real MySQL database (not mocked).
	"""
	# Build database URL from environment
	db_driver = os.getenv("MYSQL_ASYNC_DRIVER", "mysql+aiomysql")
	db_host = os.getenv("MYSQL_HOST", "127.0.0.1")
	db_port = os.getenv("MYSQL_PORT", "3307")
	db_user = os.getenv("MYSQL_USER", "root")
	db_pass = os.getenv("MYSQL_PASSWORD", "rootpassword")
	db_name = os.getenv("MYSQL_DATABASE", "ai_ticket_platform")

	database_url = f"{db_driver}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

	# Create engine
	engine = create_async_engine(
		database_url,
		echo=False,
		pool_size=10,
		max_overflow=20,
		pool_pre_ping=True,
		pool_recycle=3600,
	)

	# Create session
	AsyncSessionLocal = async_sessionmaker(
		engine, class_=AsyncSession, expire_on_commit=False
	)

	async with AsyncSessionLocal() as session:
		try:
			yield session
		finally:
			await session.close()
			await engine.dispose()


@pytest_asyncio.fixture
async def redis_client():
	"""
	Provide a direct Redis client for verification queries.
	Uses real Redis instance (not mocked).
	"""
	redis_url = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")

	client = redis.from_url(redis_url)

	try:
		# Verify connection
		await client.ping()
		logger.info("✅ Redis client connected")
		yield client
	finally:
		await client.aclose()
