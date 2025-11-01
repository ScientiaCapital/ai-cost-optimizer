"""Tests for RoutingService."""
import pytest
from app.services.routing_service import RoutingService


@pytest.fixture
def providers():
    """Mock providers dictionary."""
    return {
        "gemini": {"name": "gemini-1.5-flash"},
        "claude": {"name": "claude-3-haiku-20240307"}
    }


def test_routing_service_initialization(providers, tmp_path):
    """Test that RoutingService initializes correctly."""
    db_path = str(tmp_path / "test.db")

    service = RoutingService(db_path=db_path, providers=providers)

    assert service.engine is not None
    assert service.providers == providers
    assert service.cost_tracker is not None
