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
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ai_ticket_platform.main import app
from ai_ticket_platform.database.generated_models import Base
from ai_ticket_platform.dependencies.database import get_db


# ============================================================================
# Database Setup for Testing
# ============================================================================

TEST_DATABASE_URL = "mysql+aiomysql://root:rootpassword@localhost:3307/ai_ticket_platform"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
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


@pytest_asyncio.fixture
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
# FastAPI Test Client Setup
# ============================================================================

@pytest_asyncio.fixture
async def async_client(db_session):
    """
    Provide an async test client for making requests to the app.
    Uses the test database session.
    """
    from httpx import ASGITransport

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

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
