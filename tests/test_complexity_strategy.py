"""Tests for ComplexityStrategy."""
import pytest
from app.routing.strategy import ComplexityStrategy
from app.routing.models import RoutingContext


def test_complexity_strategy_simple_prompt():
    """Test simple prompt routes to Gemini."""
    strategy = ComplexityStrategy()
    context = RoutingContext(prompt="Hello")

    decision = strategy.route("Hello", context)

    assert decision.provider == "gemini"
    assert decision.model == "gemini-flash"
    assert decision.confidence == "medium"
    assert decision.strategy_used == "complexity"
    assert "complexity" in decision.metadata


def test_complexity_strategy_moderate_prompt():
    """Test moderate prompt routes to Claude Haiku."""
    strategy = ComplexityStrategy()
    context = RoutingContext(prompt="Explain how HTTP works")

    decision = strategy.route("Explain how HTTP works", context)

    assert decision.provider == "claude"
    assert decision.model == "claude-3-haiku"
    assert decision.confidence == "medium"


def test_complexity_strategy_complex_prompt():
    """Test complex prompt routes to Claude Sonnet."""
    strategy = ComplexityStrategy()
    long_prompt = "Analyze the architectural trade-offs between " * 10
    context = RoutingContext(prompt=long_prompt)

    decision = strategy.route(long_prompt, context)

    assert decision.provider == "claude"
    assert decision.model == "claude-3-sonnet"
    assert decision.fallback_used is False


def test_complexity_strategy_name():
    """Test strategy returns correct name."""
    strategy = ComplexityStrategy()
    assert strategy.get_name() == "complexity"
