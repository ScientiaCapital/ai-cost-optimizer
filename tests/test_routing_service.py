"""Tests for RoutingService."""
import pytest
from app.services.routing_service import RoutingService
from unittest.mock import Mock, patch, AsyncMock


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


def test_route_and_complete_cache_hit(providers, tmp_path):
    """Test route_and_complete with cache hit."""
    db_path = str(tmp_path / "test.db")
    service = RoutingService(db_path=db_path, providers=providers)

    # Mock cache hit
    with patch.object(service.cost_tracker, 'check_cache') as mock_cache:
        mock_cache.return_value = {
            "cache_key": "test123",
            "response": "Cached response",
            "provider": "gemini",
            "model": "gemini-1.5-flash",
            "complexity": "simple",
            "tokens_in": 10,
            "tokens_out": 50,
            "cost": 0.001,
            "created_at": "2025-01-01",
            "hit_count": 1
        }

        import asyncio
        result = asyncio.run(service.route_and_complete(
            prompt="Test prompt",
            auto_route=False,
            max_tokens=1000
        ))

        assert result["response"] == "Cached response"
        assert result["cache_hit"] is True
        assert result["cost"] == 0.0  # Cache hits are free
        assert result["original_cost"] == 0.001


@pytest.mark.asyncio
async def test_route_and_complete_cache_miss(providers, tmp_path):
    """Test route_and_complete with cache miss (full routing)."""
    db_path = str(tmp_path / "test.db")

    # Create mock provider with async send_message
    mock_provider = Mock()
    mock_provider.send_message = AsyncMock(return_value={
        "response": "Provider response text",
        "tokens_in": 20,
        "tokens_out": 100,
        "cost": 0.005
    })

    providers_dict = {"gemini": mock_provider}
    service = RoutingService(db_path=db_path, providers=providers_dict)

    # Mock cache miss (returns None)
    with patch.object(service.cost_tracker, 'check_cache', return_value=None):
        result = await service.route_and_complete(
            prompt="What is Python?",
            auto_route=False,  # Use complexity routing
            max_tokens=1000
        )

    # Verify cache miss response
    assert result["response"] == "Provider response text"
    assert result["cache_hit"] is False
    assert result["cost"] == 0.005
    assert result["tokens_in"] == 20
    assert result["tokens_out"] == 100
    assert mock_provider.send_message.called
