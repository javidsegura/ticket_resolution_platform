"""
Integration test conftest

Provides async HTTP client to test the running backend via ASGI transport.
Tests validate E2E behavior of the MVP pipeline without a separate test database.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from ai_ticket_platform.main import app


@pytest_asyncio.fixture
async def async_client():
    """
    Provide an async HTTP client to the running backend server.
    Uses ASGI transport for testing without real HTTP server.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
