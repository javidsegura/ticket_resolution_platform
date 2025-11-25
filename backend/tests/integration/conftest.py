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
    Provide an HTTP client configured to send requests to the application via an ASGI transport for integration tests.
    
    Yields:
        An `AsyncClient` configured with an `ASGITransport` using the application instance and a test base URL.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client