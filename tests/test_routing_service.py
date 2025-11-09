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
        assert result["request_id"] is not None  # Verify request_id is generated


@pytest.mark.asyncio
async def test_route_and_complete_cache_miss(providers, tmp_path):
    """Test route_and_complete with cache miss (full routing)."""
    db_path = str(tmp_path / "test.db")

    # Create mock provider with async complete() method
    # complete() returns (text, input_tokens, output_tokens, cost)
    mock_provider = Mock()
    mock_provider.complete = AsyncMock(return_value=(
        "Provider response text",  # response text
        20,                         # tokens_in
        100,                        # tokens_out
        0.005                       # cost
    ))

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
    assert result["request_id"] is not None  # Verify request_id is generated
    assert mock_provider.complete.called


def test_get_recommendation(providers, tmp_path):
    """Test get_recommendation returns routing decision without execution."""
    db_path = str(tmp_path / "test.db")
    service = RoutingService(db_path=db_path, providers=providers)

    prompt = "Explain quantum computing"

    with patch.object(service.engine, 'route') as mock_route:
        # Mock the routing decision
        mock_decision = Mock()
        mock_decision.provider = "claude"
        mock_decision.model = "claude-3-haiku-20240307"
        mock_decision.strategy_used = "hybrid"
        mock_decision.confidence = "high"
        mock_decision.reasoning = "Complex technical topic"
        mock_decision.metadata = {"complexity_score": 0.8}
        mock_route.return_value = mock_decision

        result = service.get_recommendation(prompt)

        # Verify method was called with auto_route=True
        mock_route.assert_called_once()
        call_args = mock_route.call_args
        assert call_args.kwargs['auto_route'] is True
        assert call_args.kwargs['prompt'] == prompt

        # Verify result structure
        assert result["provider"] == "claude"
        assert result["model"] == "claude-3-haiku-20240307"
        assert result["strategy_used"] == "hybrid"
        assert result["confidence"] == "high"
        assert result["reasoning"] == "Complex technical topic"
        assert result["metadata"] == {"complexity_score": 0.8}


def test_get_routing_metrics(providers, tmp_path):
    """Test get_routing_metrics returns comprehensive metrics."""
    db_path = str(tmp_path / "test.db")
    service = RoutingService(db_path=db_path, providers=providers)

    # Mock the metrics collector's get_metrics method
    mock_metrics = {
        "strategy_performance": {
            "complexity": {"decisions": 10, "avg_cost": 0.0012},
            "learning": {"decisions": 5, "avg_cost": 0.0008},
            "hybrid": {"decisions": 15, "avg_cost": 0.0010}
        },
        "total_decisions": 30,
        "confidence_distribution": {
            "high": 20,
            "medium": 8,
            "low": 2
        },
        "provider_usage": {
            "gemini": 12,
            "claude": 10,
            "openrouter": 8
        }
    }

    with patch.object(service.engine.metrics, 'get_metrics', return_value=mock_metrics, create=True):
        result = service.get_routing_metrics()

        # Verify complete structure
        assert result == mock_metrics
        assert "strategy_performance" in result
        assert "total_decisions" in result
        assert result["total_decisions"] == 30
        assert "confidence_distribution" in result
        assert result["confidence_distribution"]["high"] == 20
