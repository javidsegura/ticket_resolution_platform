"""
Root conftest for all tests
Provides shared fixtures and configuration

Infrastructure Note:
- Tests connect to Docker MySQL running on localhost:3307
- Start Docker containers with: docker compose -f docker-compose.yml -f docker-compose.test.yml up -d
- Requires: Colima, Docker, and docker-compose
"""

import os

# ============================================================================
# Environment Setup for Testing - MUST BE FIRST
# ============================================================================

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

# Now safe to import app after environment is configured
import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ai_ticket_platform.main import app
from ai_ticket_platform.database.generated_models import Base
from ai_ticket_platform.dependencies.database import get_db
from ai_ticket_platform.dependencies.settings import get_app_settings


# ============================================================================
# Database Setup for Testing
# ============================================================================

TEST_DATABASE_URL = "mysql+aiomysql://root:rootpassword@localhost:3307/ai_ticket_platform"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def setup_test_db():
    """
    Set up test database before running all tests.
    Creates all tables and cleans up after.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield

        # Clean up after all tests
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    finally:
        await engine.dispose()


@pytest_asyncio.fixture(loop_scope="function")
async def db_session(setup_test_db):
    """
    Provide a fresh database session for each test.
    Automatically rolls back changes after test.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()

    await engine.dispose()


# ============================================================================
# Settings Setup for Testing
# ============================================================================

class TestSettings:
    """Test settings object for dependency injection"""
    ENVIRONMENT = 'test'
    OPENAI_API_KEY = 'test-key-123'
    OPENAI_MODEL = 'gpt-4'
    SLACK_BOT_TOKEN = 'xoxb-test-token'
    SLACK_CHANNEL_ID = 'C123456789'
    DATABASE_URL = TEST_DATABASE_URL


@pytest.fixture
def test_settings():
    """Provide test settings with mocked values"""
    return TestSettings()


# ============================================================================
# FastAPI Test Client Setup
# ============================================================================

@pytest_asyncio.fixture(loop_scope="function")
async def async_client(db_session, test_settings):
    """
    Provide an async test client for making requests to the app.
    Uses the test database session.
    """
    from httpx import ASGITransport

    async def override_get_db():
        yield db_session

    async def override_get_settings():
        return test_settings

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_app_settings] = override_get_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def client(db_session):
    """
    Provide a synchronous test client for making requests to the app.
    Uses the test database session.
    """
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
