"""
Integration test conftest

Provides async HTTP client to the running backend via ASGI transport.
Tests validate E2E behavior of the MVP pipeline without a separate test database.
"""

import os


def pytest_configure(config):
	"""
	Pytest hook that runs BEFORE any imports or test collection.
	This ensures environment variables are set before app initialization.
	"""
	# Set test environment BEFORE any imports that trigger initialization
	os.environ.setdefault("ENVIRONMENT", "test")
	os.environ.setdefault("OPENAI_API_KEY", "test-key-123")
	os.environ.setdefault("OPENAI_MODEL", "gpt-4")
	os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test-token")
	os.environ.setdefault("SLACK_CHANNEL_ID", "C123456789")

	# Database configuration
	os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
	os.environ.setdefault("MYSQL_USER", "root")
	os.environ.setdefault("MYSQL_PASSWORD", "rootpassword")
	os.environ.setdefault("MYSQL_HOST", "localhost")
	os.environ.setdefault("MYSQL_PORT", "3307")
	os.environ.setdefault("MYSQL_DATABASE", "ai_ticket_platform")
	os.environ.setdefault("MYSQL_SYNC_DRIVER", "mysql+pymysql")
	os.environ.setdefault("MYSQL_ASYNC_DRIVER", "mysql+aiomysql")

	# AWS configuration (test values)
	os.environ.setdefault("AWS_ACCESS_KEY_ID", "test-key")
	os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test-secret")
	os.environ.setdefault("AWS_MAIN_REGION", "us-east-1")
	os.environ.setdefault("S3_MAIN_BUCKET_NAME", "test-bucket")

	# Chroma and Gemini configuration (test values)
	os.environ.setdefault("CHROMA_HOST", "localhost")
	os.environ.setdefault("CHROMA_PORT", "8000")
	os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")


import pytest
import pytest_asyncio
import logging
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
import redis.asyncio as redis

# DON'T import app at module level - it triggers tasks.py initialization before env vars are set
# from ai_ticket_platform.main import app

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture
async def async_client():
	"""
	Provide an async HTTP client to the running backend server.
	Uses ASGI transport for testing without real HTTP server.

	App is imported inside fixture so pytest_configure can set env vars first.
	"""
	from ai_ticket_platform.main import app  # Import here after pytest_configure runs

	transport = ASGITransport(app=app)
	async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
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

	# Create engine with NullPool to avoid event loop issues across tests
	from sqlalchemy.pool import NullPool
	engine = create_async_engine(
		database_url,
		echo=False,
		poolclass=NullPool,  # No connection pooling - each request gets fresh connection
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
