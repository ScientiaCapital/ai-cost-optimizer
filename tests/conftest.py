import pytest
import asyncio
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="function")
def client():
    """Get test client."""
    # TODO: Add database fixture override when testing endpoints that persist data
    # See: docs/plans/2025-10-30-revenue-model-production-ready.md Task 1.1 Step 2
    # For now, router tests don't interact with database so simplified version is fine
    yield TestClient(app)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
