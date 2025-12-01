"""
Root conftest for all tests
Provides shared fixtures and configuration

Infrastructure Note:
- Tests connect to Docker MySQL running on localhost:3307
- Start Docker containers with: docker compose -f docker-compose.yml -f docker-compose.test.yml up -d
- Requires: Colima, Docker, and docker-compose
"""

import pytest
import pytest_asyncio
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ai_ticket_platform.main import app
from ai_ticket_platform.database.generated_models import Base
from ai_ticket_platform.dependencies.database import get_db
from ai_ticket_platform.dependencies.settings import get_app_settings


# ============================================================================
# Environment Setup for Testing
# ============================================================================

# Set test environment before any app initialization
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("OPENAI_API_KEY", "test-key-123")
os.environ.setdefault("OPENAI_MODEL", "gpt-4")
os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test-token")
os.environ.setdefault("SLACK_CHANNEL_ID", "C123456789")


# ============================================================================
# Database Setup for Testing
# ============================================================================

TEST_DATABASE_URL = "mysql+aiomysql://root:rootpassword@localhost:3307/ai_ticket_platform"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def setup_test_db():
    """
    Create and teardown the test database schema used for the test session.
    
    Creates all tables defined on Base.metadata before tests run, drops those tables after the session completes, and ensures the underlying async engine is disposed.
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
    Provide a fresh database session scoped to a single test.
    
    This fixture depends on the session-scoped `setup_test_db` to ensure the test database schema exists. It yields a new database session to the test and rolls back any transaction state after the test completes to keep tests isolated.
    
    Parameters:
        setup_test_db: Session-scoped fixture that creates and later drops all database tables for the test run.
    
    Returns:
        AsyncSession: An asynchronous database session connected to the test database.
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
    """
    Return a TestSettings instance configured with test configuration values.
    
    Returns:
        TestSettings: An instance containing test settings (ENVIRONMENT, OPENAI_API_KEY, OPENAI_MODEL, SLACK_BOT_TOKEN, SLACK_CHANNEL_ID, DATABASE_URL).
    """
    return TestSettings()


# ============================================================================
# FastAPI Test Client Setup
# ============================================================================

@pytest_asyncio.fixture(loop_scope="function")
async def async_client(db_session, test_settings):
    """
    Create an AsyncClient for testing the FastAPI app with database and settings dependencies overridden for tests.
    
    Parameters:
        db_session (AsyncSession): An async database session to be yielded by the app's `get_db` dependency.
        test_settings (TestSettings): Test settings instance to be returned by the app's `get_app_settings` dependency.
    
    Returns:
        async_client (httpx.AsyncClient): An AsyncClient configured to send requests to the app using an ASGI transport.
    """
    from httpx import ASGITransport

    async def override_get_db():
        """
        Provide the per-test database session for dependency overrides.
        
        Returns:
            AsyncSession: The test AsyncSession bound to the test database.
        """
        yield db_session

    async def override_get_settings():
        """
        Provide the test settings instance for overriding application settings during tests.
        
        Returns:
            TestSettings: The `TestSettings` instance used by the test suite.
        """
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
    Provide a synchronous TestClient configured to use the per-test database session.
    
    Overrides the application's `get_db` dependency to yield the provided `db_session` so requests use the test database, then clears dependency overrides on teardown.
    
    Parameters:
        db_session: The per-test database session to be supplied to request handlers.
    
    Returns:
        test_client: A TestClient instance bound to the FastAPI app.
    """
    async def override_get_db():
        """
        Provide the per-test database session for dependency overrides.
        
        Returns:
            AsyncSession: The test AsyncSession bound to the test database.
        """
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()