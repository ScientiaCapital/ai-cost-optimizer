import pytest
import asyncio
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client():
    """Get test client."""
    yield TestClient(app)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
